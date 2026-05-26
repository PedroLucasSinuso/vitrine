"""Tests for GET /bi/diario/comparativo endpoint."""

from datetime import date, time, timedelta, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_transaction_source
from app.application.bi.factory import _ajustar_mesmo_dia_semana
from app.core.models.transaction import TransactionItem, OperationType


# ── Helpers ───────────────────────────────────────────────────────────────────

def _criar_item(
    document_id: str,
    data: date,
    hora: int,
    valor: float,
    qtd: float = 1.0,
    operacao: OperationType = OperationType.SALE,
) -> TransactionItem:
    """Cria um TransactionItem para teste."""
    return TransactionItem(
        document_id=document_id,
        date=data,
        time=time(hora, 0),
        operation=operacao,
        line_total=Decimal(str(valor)),
        quantity=Decimal(str(qtd)),
        product_code="789001",
        product_name="Produto Teste",
        group_name="GRUPO",
        family_name="FAMILIA",
    )


class MockTransactionSource:
    """Mock simples de TransactionSource que retorna items por dicionário de datas."""

    def __init__(self, items_por_data: dict[date, list[TransactionItem]]):
        self.items_por_data = items_por_data

    def get_items(self, start: date, end: date) -> list[TransactionItem]:
        result = []
        for d, items in self.items_por_data.items():
            if start <= d <= end:
                result.extend(items)
        return result


def _setup_mock(items_por_data: dict[date, list[TransactionItem]]):
    """Configura o mock do TransactionSource e retorna o contexto."""
    mock = MockTransactionSource(items_por_data)
    app = __import__("app.main", fromlist=["app"]).app
    app.dependency_overrides[get_transaction_source] = lambda: mock
    return mock


def _cleanup_mock():
    """Remove o override do TransactionSource."""
    app = __import__("app.main", fromlist=["app"]).app
    app.dependency_overrides.pop(get_transaction_source, None)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestDiarioComparativoCompleto:
    """Tests for complete day (not today) — YoY comparison."""

    def test_completo_receita(self, client, token_admin):
        """Complete day returns YoY comparison with correct values."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        offset = _ajustar_mesmo_dia_semana(ontem, ontem.replace(year=ontem.year - 1))

        items_atuais = [
            _criar_item("DOC1", ontem, 10, 100.0),
            _criar_item("DOC2", ontem, 14, 200.0),
        ]
        items_offset = [
            _criar_item("DOC3", offset, 10, 150.0),
        ]

        _setup_mock({ontem: items_atuais, offset: items_offset})

        try:
            resp = client.get(
                f"/bi/diario/comparativo?data_inicio={ontem.isoformat()}&data_fim={ontem.isoformat()}",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == str(ontem)
        assert data["valor"] == 300.0
        assert data["valor_offset"] == 150.0
        assert data["offset_data"] == str(offset)
        assert data["parcial_ate"] is None
        assert data["rotulo"] == "vs ano anterior"

    def test_completo_sem_dados_offset(self, client, token_admin):
        """Complete day when offset has no items returns 0.0 (not None)."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        offset = _ajustar_mesmo_dia_semana(ontem, ontem.replace(year=ontem.year - 1))

        items_atuais = [
            _criar_item("DOC1", ontem, 10, 100.0),
        ]

        _setup_mock({ontem: items_atuais})  # offset day not in the dict

        try:
            resp = client.get(
                f"/bi/diario/comparativo?data_inicio={ontem.isoformat()}&data_fim={ontem.isoformat()}",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["valor"] == 100.0
        # 0.0 = offset data loaded but no sales that day (legitimate zero)
        assert data["valor_offset"] == 0.0
        assert data["offset_data"] == str(offset)
        assert data["rotulo"] == "vs ano anterior"

    def test_completo_metrica_quantidade(self, client, token_admin):
        """Complete day with metrica=quantidade (qtd_item)."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        offset = _ajustar_mesmo_dia_semana(ontem, ontem.replace(year=ontem.year - 1))

        items_atuais = [
            _criar_item("DOC1", ontem, 10, 100.0, qtd=3.0),
            _criar_item("DOC2", ontem, 14, 200.0, qtd=2.0),
        ]

        _setup_mock({ontem: items_atuais, offset: []})

        try:
            resp = client.get(
                f"/bi/diario/comparativo?data_inicio={ontem.isoformat()}&data_fim={ontem.isoformat()}"
                f"&metrica=qtd_item",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["valor"] == 5.0  # 3 + 2

    def test_completo_qtd_tickets(self, client, token_admin):
        """Complete day with metrica=qtd_tickets."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)

        items_atuais = [
            _criar_item("TKT-001", ontem, 10, 100.0),
            _criar_item("TKT-001", ontem, 10, 50.0),   # same ticket
            _criar_item("TKT-002", ontem, 14, 200.0),
        ]

        _setup_mock({ontem: items_atuais})

        try:
            resp = client.get(
                f"/bi/diario/comparativo?data_inicio={ontem.isoformat()}&data_fim={ontem.isoformat()}"
                f"&metrica=qtd_tickets",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["valor"] == 2.0  # 2 unique tickets

    def test_completo_ticket_medio(self, client, token_admin):
        """Complete day with metrica=ticket_medio."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)

        items_atuais = [
            _criar_item("TKT-001", ontem, 10, 100.0),
            _criar_item("TKT-001", ontem, 10, 50.0),   # same ticket
            _criar_item("TKT-002", ontem, 14, 200.0),
        ]

        _setup_mock({ontem: items_atuais})

        try:
            resp = client.get(
                f"/bi/diario/comparativo?data_inicio={ontem.isoformat()}&data_fim={ontem.isoformat()}"
                f"&metrica=ticket_medio",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        # (100 + 50 + 200) / 2 tickets = 175.0
        assert data["valor"] == 175.0


class TestDiarioComparativoParcial:
    """Tests for partial day (today) — YoY with hora filter."""

    def _yoy_offset(self, data: date) -> date:
        """Calcula offset YoY com ajuste de dia da semana."""
        return _ajustar_mesmo_dia_semana(data, data.replace(year=data.year - 1))

    def test_parcial_receita(self, client, token_admin):
        """Partial day returns YoY offset with hora filter."""
        hoje = date.today()
        offset = self._yoy_offset(hoje)

        items_hoje = [
            _criar_item("DOC1", hoje, 9, 100.0),    # before cutoff
            _criar_item("DOC2", hoje, 14, 200.0),   # before cutoff
            _criar_item("DOC3", hoje, 17, 300.0),   # after cutoff (if hour < 17)
        ]

        items_offset = [
            _criar_item("DOC4", offset, 9, 50.0),
            _criar_item("DOC5", offset, 16, 150.0),  # before cutoff
            _criar_item("DOC6", offset, 18, 250.0),  # after cutoff
        ]

        # Force hora_atual = 16 (so items at hour 17+ are filtered out)
        fake_now = datetime(hoje.year, hoje.month, hoje.day, 16, 0, 0)

        _setup_mock({hoje: items_hoje, offset: items_offset})

        try:
            with patch("app.application.bi.factory.datetime") as mock_dt:
                mock_dt.now.return_value = fake_now
                mock_dt.today.return_value = hoje
                mock_dt.strptime = datetime.strptime

                resp = client.get(
                    f"/bi/diario/comparativo?data_inicio={hoje.isoformat()}&data_fim={hoje.isoformat()}",
                    headers={"Authorization": f"Bearer {token_admin}"},
                )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == str(hoje)
        assert data["valor"] == 300.0  # 100 + 200 (DOC3 at 17h is filtered out)
        assert data["valor_offset"] == 200.0  # 50 + 150 (DOC6 at 18h filtered out)
        assert data["offset_data"] == str(offset)
        assert data["parcial_ate"] is not None
        assert ":" in data["parcial_ate"]
        assert data["rotulo"] == "vs ano anterior"

    def test_parcial_metrica_quantidade(self, client, token_admin):
        """Partial day with metrica=quantidade (qtd_item)."""
        hoje = date.today()
        offset = self._yoy_offset(hoje)

        items_hoje = [
            _criar_item("DOC1", hoje, 9, 100.0, qtd=5.0),
            _criar_item("DOC2", hoje, 17, 200.0, qtd=3.0),  # filtered out
        ]

        fake_now = datetime(hoje.year, hoje.month, hoje.day, 16, 0, 0)

        _setup_mock({hoje: items_hoje, offset: []})

        try:
            with patch("app.application.bi.factory.datetime") as mock_dt:
                mock_dt.now.return_value = fake_now
                mock_dt.today.return_value = hoje
                mock_dt.strptime = datetime.strptime

                resp = client.get(
                    f"/bi/diario/comparativo?data_inicio={hoje.isoformat()}&data_fim={hoje.isoformat()}"
                    f"&metrica=qtd_item",
                    headers={"Authorization": f"Bearer {token_admin}"},
                )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["valor"] == 5.0
        assert data["rotulo"] == "vs ano anterior"

    def test_parcial_sem_dados_offset(self, client, token_admin):
        """Partial day when offset has zero items returns valor_offset = 0.0."""
        hoje = date.today()
        offset = self._yoy_offset(hoje)

        items_hoje = [
            _criar_item("DOC1", hoje, 9, 100.0),
        ]

        fake_now = datetime(hoje.year, hoje.month, hoje.day, 16, 0, 0)

        _setup_mock({hoje: items_hoje, offset: []})

        try:
            with patch("app.application.bi.factory.datetime") as mock_dt:
                mock_dt.now.return_value = fake_now
                mock_dt.today.return_value = hoje
                mock_dt.strptime = datetime.strptime

                resp = client.get(
                    f"/bi/diario/comparativo?data_inicio={hoje.isoformat()}&data_fim={hoje.isoformat()}",
                    headers={"Authorization": f"Bearer {token_admin}"},
                )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["valor"] == 100.0
        assert data["valor_offset"] == 0.0
        assert data["offset_data"] == str(offset)


class TestDiarioComparativoEdgeCases:
    """Edge cases for the endpoint."""

    def test_periodo_unico_dia(self, client, token_admin):
        """Period with a single day works (data_inicio == data_fim)."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        offset = _ajustar_mesmo_dia_semana(ontem, ontem.replace(year=ontem.year - 1))

        items = [_criar_item("DOC1", ontem, 10, 150.0)]
        items_offset = [_criar_item("DOC2", offset, 10, 120.0)]

        _setup_mock({ontem: items, offset: items_offset})

        try:
            resp = client.get(
                f"/bi/diario/comparativo?data_inicio={ontem.isoformat()}&data_fim={ontem.isoformat()}",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == str(ontem)
        assert data["valor"] == 150.0
        assert data["rotulo"] == "vs ano anterior"

    def test_periodo_vazio(self, client, token_admin):
        """Period with no items returns zeros for both values."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)

        _setup_mock({})

        try:
            resp = client.get(
                f"/bi/diario/comparativo?data_inicio={ontem.isoformat()}&data_fim={ontem.isoformat()}",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["valor"] == 0.0
        # 0.0 = no sales; not None = data loaded successfully
        assert data["valor_offset"] == 0.0

    def test_sem_items_no_ultimo_dia(self, client, token_admin):
        """Last day has no items but earlier days do."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)
        anteontem = hoje - timedelta(days=2)
        offset = _ajustar_mesmo_dia_semana(ontem, ontem.replace(year=ontem.year - 1))

        items_anteontem = [_criar_item("DOC1", anteontem, 10, 500.0)]
        items_offset = [_criar_item("DOC2", offset, 10, 300.0)]

        _setup_mock({anteontem: items_anteontem, ontem: [], offset: items_offset})

        try:
            resp = client.get(
                f"/bi/diario/comparativo?data_inicio={anteontem.isoformat()}&data_fim={ontem.isoformat()}",
                headers={"Authorization": f"Bearer {token_admin}"},
            )
        finally:
            _cleanup_mock()

        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == str(ontem)
        assert data["valor"] == 0.0
        assert data["rotulo"] == "vs ano anterior"

    def test_periodo_excede_limite(self, client, token_admin):
        """Period exceeding 180 days returns 400."""
        hoje = date.today()
        inicio = hoje - timedelta(days=200)

        resp = client.get(
            f"/bi/diario/comparativo?data_inicio={inicio.isoformat()}&data_fim={hoje.isoformat()}",
            headers={"Authorization": f"Bearer {token_admin}"},
        )

        assert resp.status_code == 400

    def test_data_fim_antes_data_inicio(self, client, token_admin):
        """data_fim before data_inicio returns 400."""
        hoje = date.today()
        ontem = hoje - timedelta(days=1)

        resp = client.get(
            f"/bi/diario/comparativo?data_inicio={hoje.isoformat()}&data_fim={ontem.isoformat()}",
            headers={"Authorization": f"Bearer {token_admin}"},
        )

        assert resp.status_code == 400

    def test_requer_autenticacao(self, client):
        """Unauthenticated request returns 401."""
        hoje = date.today()

        resp = client.get(
            f"/bi/diario/comparativo?data_inicio={hoje.isoformat()}&data_fim={hoje.isoformat()}",
        )

        assert resp.status_code == 401

    def test_requer_supervisor(self, client, token_operador):
        """Operador role returns 403."""
        hoje = date.today()

        resp = client.get(
            f"/bi/diario/comparativo?data_inicio={hoje.isoformat()}&data_fim={hoje.isoformat()}",
            headers={"Authorization": f"Bearer {token_operador}"},
        )

        assert resp.status_code == 403
