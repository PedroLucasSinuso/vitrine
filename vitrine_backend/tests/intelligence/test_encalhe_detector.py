"""Tests for the EncalheDetector."""
from datetime import date, timedelta
from unittest.mock import MagicMock
from app.application.intelligence.detectores.encalhe import EncalheDetector
from app.domain.models.produto import Produto
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


def _make_transacao(codigo: str) -> MagicMock:
    t = MagicMock()
    t.product_code = codigo
    t.internal_code = None
    return t


class TestEncalheDetector:
    def setup_method(self):
        self.detector = EncalheDetector()
        self.hoje = date(2026, 5, 27)
        self.mes_atras = self.hoje - timedelta(days=31)

    def test_sem_produtos_retorna_lista_vazia(self, db_session):
        """Nenhum produto cadastrado retorna lista vazia."""
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produtos_sem_estoque_sao_ignorados(self, db_session):
        """Produtos com estoque 0 não entram na análise."""
        _make_produto(db_session, "P001", estoque=0)
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produto_inativo_ignorado(self, db_session):
        """Produtos inativos não entram na análise."""
        p = _make_produto(db_session, "P001", estoque=5)
        p.ativo = False
        db_session.commit()
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produto_que_vendeu_nao_aparece(self, db_session):
        """Produto que vendeu no período não deve ser encalhado."""
        _make_produto(db_session, "P001", estoque=5)
        source = MagicMock()
        source.get_items.return_value = [_make_transacao("P001")]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado == []

    def test_produto_sem_venda_aparece(self, db_session):
        """Produto com estoque e sem venda deve ser listado."""
        _make_produto(db_session, "P001", nome="ProdutoA", estoque=5, preco_custo=100.0)
        source = MagicMock()
        source.get_items.return_value = [_make_transacao("OUTRO")]
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) == 1
        assert resultado[0]["nome"] == "ProdutoA"
        assert resultado[0]["valor_estimado"] == 500.0  # 5 * 100

    def test_ordenacao_por_valor_decrescente(self, db_session):
        """Resultados devem vir ordenados por valor estimado, maior primeiro."""
        _make_produto(db_session, "P001", nome="Barato", estoque=1, preco_custo=10.0)
        _make_produto(db_session, "P002", nome="Caro", estoque=1, preco_custo=1000.0)
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert resultado[0]["nome"] == "Caro"
        assert resultado[1]["nome"] == "Barato"

    def test_limite_de_itens(self, db_session):
        """Deve retornar no máximo LIMITE_ITENS (15)."""
        for i in range(20):
            _make_produto(db_session, f"P{i:03d}", nome=f"Produto {i}", estoque=1, preco_custo=10.0)
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        assert len(resultado) <= 15

    def test_grupo_ignorado_nao_aparece_no_resultado(self, db_session):
        """Produto de grupo ignorado (ex: LOJA) não deve aparecer no encalhe."""
        # Cria dois produtos: um do grupo LOJA e outro do grupo BEBIDAS
        _make_produto(db_session, "SACOLA", nome="SACOLA LEI RIO 37X50 C/1000", estoque=50, preco_custo=10.0, grupo="LOJA")
        _make_produto(db_session, "COCA", nome="Coca Cola 2L", estoque=50, preco_custo=5.0, grupo="BEBIDAS")
        # Configura ignored_groups
        set_many(db_session, {"ignored_groups": "LOJA, USO PESSOAL"})
        source = MagicMock()
        source.get_items.return_value = []
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        # SACOLA (LOJA) deve ser filtrada, COCA (BEBIDAS) deve aparecer
        codigos = [r["codigo"] for r in resultado]
        assert "SACOLA" not in codigos, "LOJA deveria ter sido filtrado"
        assert "COCA" in codigos, "BEBIDAS não deveria ser filtrado"

    def test_periodo_de_analise_correto(self, db_session):
        """Deve analisar vendas nos últimos 30 dias a partir de data_fim."""
        _make_produto(db_session, "P001", estoque=5)
        source = MagicMock()
        resultado = self.detector.detectar(db_session, source, self.mes_atras, self.hoje)
        # Verifica que source.get_items foi chamado com o período correto
        periodo_esperado_inicio = self.hoje - timedelta(days=30)
        fonte_items_call = source.get_items.call_args
        assert fonte_items_call is not None
        arg_inicio, arg_fim = fonte_items_call[0]
        assert arg_inicio == periodo_esperado_inicio
        assert arg_fim == self.hoje
