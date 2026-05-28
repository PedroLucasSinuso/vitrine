"""Tests for the SazonalidadeDetector."""
from datetime import date, timedelta
from unittest.mock import MagicMock
from app.application.intelligence.detectores.sazonalidade import SazonalidadeDetector
from app.core.models.transaction import OperationType


def _make_transacao(codigo: str, qtd=1.0, valor=100.0, nome="Produto", grupo="GRUPO", familia="FAMILIA") -> MagicMock:
    t = MagicMock()
    t.product_code = codigo
    t.operation = OperationType.SALE
    t.quantity = qtd
    t.line_total = valor
    t.product_name = nome
    t.group_name = grupo
    t.family_name = familia
    return t


class TestSazonalidadeDetector:
    def setup_method(self):
        self.detector = SazonalidadeDetector()
        self.hoje = date(2026, 5, 27)
        self.inicio = date(2026, 5, 1)
        self.fim = date(2026, 5, 27)

    def test_sem_transacoes_retorna_vazio(self, db_session):
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_crescimento_abaixo_30_ignorado(self, db_session):
        source = MagicMock()
        source.get_items.side_effect = [
            [_make_transacao("P001", qtd=10)],   # atual
            [_make_transacao("P001", qtd=9)],    # anterior
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_crescimento_acima_30_aparece(self, db_session):
        source = MagicMock()
        source.get_items.side_effect = [
            [_make_transacao("P001", qtd=15)],   # atual
            [_make_transacao("P001", qtd=10)],   # anterior
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert len(resultado) == 1
        assert resultado[0]["codigo"] == "P001"
        assert resultado[0]["crescimento_qtd"] >= 0.30

    def test_sem_historico_ignorado(self, db_session):
        source = MagicMock()
        source.get_items.side_effect = [
            [_make_transacao("P001", qtd=15)],   # atual
            [],                                   # anterior
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_ordenacao_por_crescimento(self, db_session):
        source = MagicMock()
        source.get_items.side_effect = [
            [_make_transacao("P001", qtd=20), _make_transacao("P002", qtd=30)],  # atual
            [_make_transacao("P001", qtd=10), _make_transacao("P002", qtd=5)],   # anterior
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert len(resultado) == 2
        assert resultado[0]["codigo"] == "P002"  # 500% > 100%

    def test_limite_de_itens(self, db_session):
        source = MagicMock()
        atuais = [_make_transacao(f"P{i:03d}", qtd=20) for i in range(15)]
        anteriores = [_make_transacao(f"P{i:03d}", qtd=5) for i in range(15)]
        source.get_items.side_effect = [atuais, anteriores]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert len(resultado) <= 10
