"""Tests for the OportunidadeBDetector."""
from datetime import date, timedelta
from unittest.mock import MagicMock
from app.application.intelligence.detectores.oportunidade_b import OportunidadeBDetector
from app.core.models.transaction import OperationType


def _make_transacao(codigo: str, valor=100.0, nome="Produto") -> MagicMock:
    t = MagicMock()
    t.product_code = codigo
    t.operation = OperationType.SALE
    t.quantity = 1.0
    t.line_total = valor
    t.product_name = nome
    return t


class TestOportunidadeBDetector:
    def setup_method(self):
        self.detector = OportunidadeBDetector()
        self.hoje = date(2026, 5, 27)
        self.inicio = date(2026, 5, 1)
        self.fim = date(2026, 5, 27)

    def test_sem_dados_retorna_vazio(self, db_session):
        source = MagicMock()
        source.get_curva_abc_aggregates.return_value = []
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_com_abc_b_com_margem_maior_que_a_aparece(self, db_session):
        """Itens B com margem maior que a média de A devem ser listados."""
        source = MagicMock()
        # Produtos A (80% da receita): margem 25%
        # Produtos B (15% da receita): margem 40%
        abc = [
            {"codigo": "A001", "nome": "ProdutoA1", "receita": 5000.0, "margem": 0.25},
            {"codigo": "A002", "nome": "ProdutoA2", "receita": 3000.0, "margem": 0.25},
            {"codigo": "B001", "nome": "ProdutoB1", "receita": 1000.0, "margem": 0.40},
            {"codigo": "B002", "nome": "ProdutoB2", "receita": 500.0, "margem": 0.35},
        ]
        source.get_curva_abc_aggregates.return_value = abc
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert len(resultado) >= 1
        assert resultado[0]["margem_atual"] > resultado[0]["margem_media_a"]

    def test_b_com_margem_menor_que_a_ignorado(self, db_session):
        """Itens B com margem abaixo da média A não devem ser listados."""
        source = MagicMock()
        abc = [
            {"codigo": "A001", "nome": "ProdutoA1", "receita": 8000.0, "margem": 0.35},
            {"codigo": "B001", "nome": "ProdutoB1", "receita": 1000.0, "margem": 0.20},
        ]
        source.get_curva_abc_aggregates.return_value = abc
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_fallback_manual_sem_abc(self, db_session):
        """Quando get_curva_abc_aggregates retorna None, deve usar fallback manual."""
        source = MagicMock()
        source.get_curva_abc_aggregates.return_value = None
        source.get_items.return_value = [
            _make_transacao("P001", valor=100, nome="Barato"),
            _make_transacao("P002", valor=10, nome="MuitoBarato"),
        ]
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        # Fallback manual retorna itens com participacao <= 15%
        assert len(resultado) >= 1

    def test_fallback_sem_transacoes_retorna_vazio(self, db_session):
        source = MagicMock()
        source.get_curva_abc_aggregates.return_value = None
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert resultado == []

    def test_limite_de_itens(self, db_session):
        source = MagicMock()
        abc = [
            {"codigo": f"A{i:03d}", "nome": f"ProdutoA{i}", "receita": 1000.0, "margem": 0.20}
            for i in range(20)
        ]
        abc += [
            {"codigo": f"B{i:03d}", "nome": f"ProdutoB{i}", "receita": 100.0, "margem": 0.40}
            for i in range(10)
        ]
        source.get_curva_abc_aggregates.return_value = abc
        resultado = self.detector.detectar(db_session, source, self.inicio, self.fim)
        assert len(resultado) <= 5
