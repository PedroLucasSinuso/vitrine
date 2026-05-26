"""Performance test: BI criar_dominio com muitos itens."""
import time
from datetime import date, time as dtime
from decimal import Decimal
from unittest.mock import MagicMock
import pytest

from app.application.bi.factory import criar_dominio
from app.core.models.transaction import TransactionItem, OperationType
from app.core.interfaces.source import TransactionSource


def _gerar_itens(qtd: int) -> list[TransactionItem]:
    """Gera N TransactionItems de venda."""
    items = []
    for i in range(qtd):
        items.append(TransactionItem(
            document_id=str(i // 5),
            date=date(2026, 1, 1),
            time=dtime(8 + i % 10, 0),
            operation=OperationType.SALE,
            is_canceled=False,
            product_code=str(i),
            product_name=f"Produto {i}",
            group_name="GRUPO",
            family_name="FAMILIA",
            quantity=Decimal("1.0"),
            line_total=Decimal("10.00"),
            document_total=Decimal("50.00"),
            external_document_id=None,
        ))
    return items


def test_criar_dominio_100k_itens():
    """criar_dominio com 100k itens deve completar em < 2s."""
    mock_source = MagicMock(spec=TransactionSource)
    mock_source.get_items.return_value = _gerar_itens(100_000)
    # get_kpi_aggregates retorna None para forçar full load
    mock_source.get_kpi_aggregates.return_value = None

    start = time.time()
    dominio = criar_dominio(mock_source, date(2026, 1, 1), date(2026, 1, 31))
    elapsed = time.time() - start

    assert len(dominio.vendas.items) == 100_000
    assert elapsed < 2.0, f"criar_dominio levou {elapsed:.2f}s (limite: 2s)"


def test_criar_dominio_10k_itens():
    """criar_dominio com 10k itens deve ser muito rápido (< 0.5s)."""
    mock_source = MagicMock(spec=TransactionSource)
    mock_source.get_items.return_value = _gerar_itens(10_000)
    mock_source.get_kpi_aggregates.return_value = None

    start = time.time()
    dominio = criar_dominio(mock_source, date(2026, 1, 1), date(2026, 1, 31))
    elapsed = time.time() - start

    assert len(dominio.vendas.items) == 10_000
    assert elapsed < 0.5, f"criar_dominio levou {elapsed:.2f}s (limite: 0.5s)"


def test_criar_dominio_com_trocas_e_vendas_misturados():
    """Dominio com vendas e trocas deve separar corretamente."""
    from app.core.models.transaction import OperationType

    items = []
    for i in range(100):
        op = OperationType.SALE if i < 80 else OperationType.RETURN
        items.append(TransactionItem(
            document_id=str(i),
            date=date(2026, 1, 1),
            time=dtime(10, 0),
            operation=op,
            is_canceled=False,
            product_code=str(i),
            product_name=f"Prod {i}",
            group_name="G",
            family_name="F",
            quantity=Decimal("1.0"),
            line_total=Decimal("10.00"),
            document_total=Decimal("10.00"),
        ))

    mock_source = MagicMock(spec=TransactionSource)
    mock_source.get_items.return_value = items
    mock_source.get_kpi_aggregates.return_value = None

    start = time.time()
    dominio = criar_dominio(mock_source, date(2026, 1, 1), date(2026, 1, 31))
    elapsed = time.time() - start

    assert len(dominio.vendas.items) == 80
    assert len(dominio.trocas.items) == 20
    assert elapsed < 0.5
