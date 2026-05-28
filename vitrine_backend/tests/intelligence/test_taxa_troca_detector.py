"""Tests for the TaxaTrocaDetector."""
from datetime import date, timedelta
from unittest.mock import MagicMock
from app.application.intelligence.detectores.taxa_troca import TaxaTrocaDetector
from app.core.models.transaction import OperationType


def _make_transacao(codigo: str, operacao: OperationType, qtd=1.0, nome="Produto", grupo="GRUPO", familia="FAMILIA") -> MagicMock:
    t = MagicMock()
    t.product_code = codigo
    t.operation = operacao
    t.quantity = qtd
    t.line_total = 100.0
    t.product_name = nome
    t.group_name = grupo
    t.family_name = familia
    return t


class TestTaxaTrocaDetector:
    def setup_method(self):
        self.detector = TaxaTrocaDetector()
        self.hoje = date(2026, 5, 27)
        self.mes_atras = self.hoje - timedelta(days=30)

    def test_sem_transacoes_retorna_vazio(self, db_session):
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produto_sem_troca_ignorado(self, db_session):
        source = MagicMock()
        source.get_items.return_value = [
            _make_transacao("P001", OperationType.SALE, qtd=10),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produto_com_troca_acima_limiar_aparece(self, db_session):
        source = MagicMock()
        source.get_items.return_value = [
            _make_transacao("P001", OperationType.SALE, qtd=5),
            _make_transacao("P001", OperationType.RETURN, qtd=2),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) == 1
        assert resultado[0]["codigo"] == "P001"
        assert resultado[0]["taxa"] >= 0.10

    def test_taxa_abaixo_limiar_ignorada(self, db_session):
        source = MagicMock()
        source.get_items.return_value = [
            _make_transacao("P001", OperationType.SALE, qtd=100),
            _make_transacao("P001", OperationType.RETURN, qtd=1),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_ordenacao_por_taxa_decrescente(self, db_session):
        source = MagicMock()
        source.get_items.return_value = [
            _make_transacao("P001", OperationType.SALE, qtd=5),
            _make_transacao("P001", OperationType.RETURN, qtd=3),
            _make_transacao("P002", OperationType.SALE, qtd=10),
            _make_transacao("P002", OperationType.RETURN, qtd=2),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) == 2
        assert resultado[0]["codigo"] == "P001"
        assert resultado[1]["codigo"] == "P002"

    def test_limite_de_itens(self, db_session):
        source = MagicMock()
        items = []
        for i in range(20):
            items.append(_make_transacao(f"P{i:03d}", OperationType.SALE, qtd=5))
            items.append(_make_transacao(f"P{i:03d}", OperationType.RETURN, qtd=2))
        source.get_items.return_value = items
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) <= 10
