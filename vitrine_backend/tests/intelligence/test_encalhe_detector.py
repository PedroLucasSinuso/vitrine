"""Tests for the EncalheDetector.

A nova lógica do detector:
  - Busca TODAS as operações dos últimos 90d (venda, devolução, perda, consumo)
  - SKUs sem nenhuma movimentação em 90d são ignorados (produtos mortos)
  - SKUs com venda nos últimos 30d são ignorados (ainda vendendo)
  - SKUs ativos (movimentaram em 90d) que NÃO venderam em 30d → encalhados
"""
from datetime import date, timedelta
from unittest.mock import MagicMock
from app.application.intelligence.detectores.encalhe import EncalheDetector
from app.domain.models.produto import Produto
from app.core.models.transaction import OperationType
from app.application.config_service import set_many


def _make_produto(db, codigo, nome="Produto Teste", estoque=10, grupo="GRUPO", preco_custo=50.0, familia="FAMILIA"):
    p = Produto(
        codigo_chamada=codigo,
        nome=nome,
        grupo=grupo,
        familia=familia,
        preco_venda=preco_custo * 1.5,
        preco_custo=preco_custo,
        estoque=estoque,
        ativo=True,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _make_transacao(codigo: str, operation: OperationType = OperationType.SALE, days_ago: int = 5) -> MagicMock:
    """Cria uma transação mockada para testes.

    Args:
        codigo: Código do produto (product_code)
        operation: Tipo de operação (SALE, RETURN, etc.)
        days_ago: Há quantos dias a transação ocorreu (relativo a self.hoje)
    """
    t = MagicMock()
    t.product_code = codigo
    t.operation = operation
    t.date = date(2026, 5, 27) - timedelta(days=days_ago)
    t.internal_code = None
    return t


class TestEncalheDetector:
    def setup_method(self):
        self.detector = EncalheDetector()
        self.hoje = date(2026, 5, 27)
        self.mes_atras = self.hoje - timedelta(days=31)

    # ── Casos base ──

    def test_sem_produtos_retorna_lista_vazia(self, db_session):
        """Nenhum produto cadastrado retorna lista vazia."""
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_sem_transacoes_retorna_lista_vazia(self, db_session):
        """Se não há transações nos últimos 90d, nenhum produto é considerado ativo."""
        _make_produto(db_session, "P001", estoque=5)
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produtos_sem_estoque_sao_ignorados(self, db_session):
        """Produtos com estoque 0 não entram na análise."""
        _make_produto(db_session, "P001", estoque=0)
        source = MagicMock()
        source.get_items.return_value = [_make_transacao("P001", days_ago=60)]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produto_inativo_ignorado(self, db_session):
        """Produtos inativos não entram na análise."""
        p = _make_produto(db_session, "P001", estoque=5)
        p.ativo = False
        db_session.commit()
        source = MagicMock()
        source.get_items.return_value = [_make_transacao("P001", days_ago=60)]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    # ── Lógica de ativo + venda ──

    def test_produto_que_vendeu_recentemente_nao_aparece(self, db_session):
        """Produto com venda nos últimos 30 dias não deve ser encalhado."""
        _make_produto(db_session, "P001", estoque=5)
        source = MagicMock()
        source.get_items.return_value = [
            _make_transacao("P001", operation=OperationType.SALE, days_ago=5),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produto_morto_sem_movimento_ignorado(self, db_session):
        """SKU sem nenhuma movimentação em 90d é ignorado (produto morto/defasado)."""
        _make_produto(db_session, "P001", nome="PEITO PERU DEFUMADO", estoque=200, preco_custo=50.0)
        source = MagicMock()
        # Só "OUTRO" teve movimentação — P001 está morto
        source.get_items.return_value = [
            _make_transacao("OUTRO", operation=OperationType.SALE, days_ago=5),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produto_ativo_sem_venda_aparece(self, db_session):
        """Produto ativo (vendeu em 90d) mas sem venda em 30d é encalhado."""
        _make_produto(db_session, "P001", nome="ProdutoA", estoque=5, preco_custo=100.0)
        source = MagicMock()
        source.get_items.return_value = [
            _make_transacao("P001", operation=OperationType.SALE, days_ago=60),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) == 1
        assert resultado[0]["nome"] == "ProdutoA"
        assert resultado[0]["valor_estimado"] == 500.0  # 5 * 100
        assert resultado[0]["dias_parado"] == 60  # última venda foi há 60 dias

    def test_dias_parado_real(self, db_session):
        """dias_parado deve refletir a última venda real, não hardcoded."""
        _make_produto(db_session, "P001", nome="ProdutoA", estoque=5, preco_custo=100.0)
        source = MagicMock()
        # Última venda foi há 45 dias → dias_parado deve ser 45
        source.get_items.return_value = [
            _make_transacao("P001", operation=OperationType.SALE, days_ago=45),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) == 1
        assert resultado[0]["dias_parado"] == 45

    def test_ultima_venda_mais_recente_e_usada(self, db_session):
        """Se há múltiplas vendas, usa a mais recente para dias_parado."""
        _make_produto(db_session, "P001", nome="ProdutoA", estoque=5, preco_custo=100.0)
        source = MagicMock()

        # Venda mais recente foi há 10 dias → não é encalhado (vendeu nos últimos 30d)
        source.get_items.return_value = [
            _make_transacao("P001", operation=OperationType.SALE, days_ago=60),
            _make_transacao("P001", operation=OperationType.SALE, days_ago=10),
            _make_transacao("P001", operation=OperationType.SALE, days_ago=45),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

        # Venda mais recente foi há 35 dias → é encalhado (fora dos 30d)
        source.get_items.return_value = [
            _make_transacao("P001", operation=OperationType.SALE, days_ago=60),
            _make_transacao("P001", operation=OperationType.SALE, days_ago=35),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) == 1
        assert resultado[0]["dias_parado"] == 35

    # ── Ordenação e limites ──

    def test_ordenacao_por_valor_decrescente(self, db_session):
        """Resultados devem vir ordenados por valor estimado, maior primeiro."""
        _make_produto(db_session, "P001", nome="Barato", estoque=2, preco_custo=10.0)
        _make_produto(db_session, "P002", nome="Caro", estoque=2, preco_custo=1000.0)
        source = MagicMock()
        # Ambos ativos (venderam uma vez há 60d) mas sem venda recente (30d)
        source.get_items.return_value = [
            _make_transacao("P001", operation=OperationType.SALE, days_ago=60),
            _make_transacao("P002", operation=OperationType.SALE, days_ago=60),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) == 2
        assert resultado[0]["nome"] == "Caro"
        assert resultado[1]["nome"] == "Barato"

    def test_limite_de_itens(self, db_session):
        """Deve retornar no máximo LIMITE_ITENS (15)."""
        for i in range(20):
            _make_produto(db_session, f"P{i:03d}", nome=f"Produto {i}", estoque=2, preco_custo=10.0)
        source = MagicMock()
        # Todos ativos (venderam há 60d), nenhum vendeu nos últimos 30d
        source.get_items.return_value = [
            _make_transacao(f"P{i:03d}", operation=OperationType.SALE, days_ago=60)
            for i in range(20)
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) <= 15

    # ── Grupos ignorados ──

    def test_grupo_ignorado_nao_aparece_no_resultado(self, db_session):
        """Produto de grupo ignorado (ex: LOJA) não deve aparecer no encalhe."""
        _make_produto(db_session, "SACOLA", nome="SACOLA LEI RIO 37X50 C/1000", estoque=50, preco_custo=10.0, grupo="LOJA")
        _make_produto(db_session, "COCA", nome="Coca Cola 2L", estoque=50, preco_custo=5.0, grupo="BEBIDAS")
        set_many(db_session, {"ignored_groups": "LOJA, USO PESSOAL"})
        source = MagicMock()
        source.get_items.return_value = [
            _make_transacao("SACOLA", operation=OperationType.SALE, days_ago=60),
            _make_transacao("COCA", operation=OperationType.SALE, days_ago=60),
        ]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        codigos = [r["codigo"] for r in resultado]
        assert "SACOLA" not in codigos, "LOJA deveria ter sido filtrado"
        assert "COCA" in codigos, "BEBIDAS não deveria ser filtrado"

    # ── Período da query ──

    def test_periodo_de_analise_90d(self, db_session):
        """Deve buscar transações dos últimos 90 dias a partir de data_fim."""
        _make_produto(db_session, "P001", estoque=5)
        source = MagicMock()
        source.get_items.return_value = []
        self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        periodo_esperado = self.hoje - timedelta(days=90)
        assert source.get_items.called
        arg_inicio, arg_fim = source.get_items.call_args[0]
        assert arg_inicio == periodo_esperado
        assert arg_fim == self.hoje
