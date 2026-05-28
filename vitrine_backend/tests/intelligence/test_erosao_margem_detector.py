"""Tests for the ErosaoMargemDetector — agora usa unit_cost do TransactionItem,
não mais Produto.preco_custo do SQLite."""
from datetime import date, timedelta
from unittest.mock import MagicMock
from app.application.intelligence.detectores.erosao_margem import ErosaoMargemDetector
from app.core.models.transaction import OperationType


def _make_transacao(codigo: str, qtd=1.0, valor=100.0, custo=50.0) -> MagicMock:
    t = MagicMock()
    t.product_code = codigo
    t.operation = OperationType.SALE
    t.quantity = qtd
    t.line_total = valor
    t.unit_cost = custo
    t.product_name = ""
    return t


class TestErosaoMargemDetector:
    def setup_method(self):
        self.detector = ErosaoMargemDetector()
        self.hoje = date(2026, 5, 27)
        self.inicio = date(2026, 5, 1)
        self.fim = date(2026, 5, 27)

    def test_sem_transacoes_retorna_vazio(self, db_session):
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_margem_estavel_ignorada(self, db_session):
        """Margem sem queda significativa não deve aparecer."""
        source = MagicMock()
        source.get_items.side_effect = [
            [_make_transacao("P001", qtd=10, valor=1000.0, custo=50.0)],
            [_make_transacao("P001", qtd=10, valor=1000.0, custo=50.0)],
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_queda_de_margem_aparece(self, db_session):
        """Queda de margem > 5pp deve ser detectada."""
        source = MagicMock()
        source.get_items.side_effect = [
            [_make_transacao("P001", qtd=10, valor=1000.0, custo=70.0)],   # preco medio = 100, margem = 30%
            [_make_transacao("P001", qtd=10, valor=2000.0, custo=70.0)],   # preco medio = 200, margem = 65%
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert len(resultado) == 1
        assert resultado[0]["codigo"] == "P001"
        assert resultado[0]["variacao_pp"] <= -5

    def test_vendas_insuficientes_ignoradas(self, db_session):
        """Menos de 5 unidades vendidas deve ser ignorado."""
        source = MagicMock()
        source.get_items.side_effect = [
            [_make_transacao("P001", qtd=2, valor=200.0, custo=70.0)],
            [_make_transacao("P001", qtd=2, valor=300.0, custo=70.0)],
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_produto_sem_custo_ignorado(self, db_session):
        """Produto sem custo (unit_cost <= 0) deve ser ignorado."""
        source = MagicMock()
        source.get_items.side_effect = [
            [_make_transacao("P001", qtd=10, valor=1000.0, custo=0.0)],
            [_make_transacao("P001", qtd=10, valor=2000.0, custo=0.0)],
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_limite_de_itens(self, db_session):
        source = MagicMock()
        atuais = [_make_transacao(f"P{i:03d}", qtd=10, valor=1000.0, custo=70.0) for i in range(15)]
        anteriores = [_make_transacao(f"P{i:03d}", qtd=10, valor=2000.0, custo=70.0) for i in range(15)]
        source.get_items.side_effect = [atuais, anteriores]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert len(resultado) <= 10

    def test_custo_maior_que_venda_ignorado(self, db_session):
        """Produto com custo > preço médio (dado errado) deve ser ignorado."""
        source = MagicMock()
        source.get_items.side_effect = [
            [_make_transacao("P001", qtd=10, valor=100.0, custo=200.0)],   # custo=200 >> venda=10
            [_make_transacao("P001", qtd=10, valor=200.0, custo=200.0)],   # custo=200 = venda=20
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []
