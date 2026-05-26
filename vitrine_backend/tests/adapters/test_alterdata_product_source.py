"""Tests for AlterdataProductSource with mocked engine and queries."""

from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text

from app.adapters.alterdata.product_source import AlterdataProductSource
from app.core.models.product import Product


# ── Helpers ──────────────────────────────────────────────────────────────────

def _criar_engine():
    """Cria engine SQLite :memory: com tabelas (sem schema — SQLite não suporta)."""
    engine = create_engine("sqlite://", future=True)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE detalhe (
                cdprincipal TEXT, dsdetalhe TEXT, vlprecovenda REAL,
                vlprecocusto REAL, stdetalheativo INTEGER, idfamilia INTEGER,
                idproduto INTEGER, iddetalhe INTEGER
            )
        """))
        conn.execute(text("""
            CREATE TABLE produto (idproduto INTEGER, idgrupo INTEGER)
        """))
        conn.execute(text("""
            CREATE TABLE grupo (idgrupo INTEGER, nmgrupo TEXT)
        """))
        conn.execute(text("""
            CREATE TABLE familia (idfamilia INTEGER, dsfamilia TEXT)
        """))
        conn.execute(text("""
            CREATE TABLE estoque (iddetalhe INTEGER, qtestoque REAL, dtreferencia TEXT)
        """))
        conn.execute(text("""
            CREATE TABLE codigos (iddetalhe INTEGER, dscodigo TEXT)
        """))
        conn.commit()
    return engine


def _mock_queries_simples():
    """Retorna queries SQL simplificadas que funcionam no SQLite.

    Em vez de LEFT JOIN + GROUP BY + subquery, usamos SELECT direto
    das tabelas com os mesmos alias de coluna que o adapter espera.
    Nota: Remove o prefixo '' porque SQLite não suporta schemas.
    """
    produto_sql = """
        SELECT
            d.cdprincipal       as codigo_chamada,
            COALESCE(g.nmgrupo, 'SEM GRUPO') as grupo,
            COALESCE(f.dsfamilia, 'SEM FAMILIA') as familia,
            d.dsdetalhe         as nome,
            d.vlprecovenda      as preco_venda,
            d.vlprecocusto      as preco_custo,
            COALESCE(e.qtestoque, 0.0) as estoque,
            COALESCE(d.stdetalheativo, 1) as ativo
        FROM detalhe d
        LEFT JOIN familia f   ON d.idfamilia = f.idfamilia
        LEFT JOIN produto p   ON d.idproduto = p.idproduto
        LEFT JOIN grupo   g   ON p.idgrupo = g.idgrupo
        LEFT JOIN estoque e   ON d.iddetalhe = e.iddetalhe
    """
    codigo_sql = """
        SELECT
            c.dscodigo as codigo,
            d.cdprincipal as codigo_chamada
        FROM codigos c
        JOIN detalhe d ON c.iddetalhe = d.iddetalhe
    """
    return produto_sql, codigo_sql


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    return _criar_engine()


@pytest.fixture
def source(engine):
    """Cria AlterdataProductSource com queries mockadas."""
    produto_sql, codigo_sql = _mock_queries_simples()
    with patch.object(AlterdataProductSource, '_load_query') as mock_load:
        mock_load.side_effect = lambda name: {
            "produto": produto_sql,
            "codigo": codigo_sql,
        }[name]
        yield AlterdataProductSource(engine)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestGetAllProducts:
    """Testes para AlterdataProductSource.get_all_products()."""

    def test_retorna_lista_com_um_produto(self, engine, source):
        """Deve retornar lista com 1 Product com dados preenchidos."""
        # Arrange
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO detalhe
                VALUES ('123', 'Produto Teste', 10.50, 5.00, 1, 1, 1, 1)
            """))
            conn.execute(text("INSERT INTO produto VALUES (1, 1)"))
            conn.execute(text("INSERT INTO grupo VALUES (1, 'GRUPO A')"))
            conn.execute(text("INSERT INTO familia VALUES (1, 'FAMILIA X')"))
            conn.execute(text("INSERT INTO estoque VALUES (1, 100.0, '2026-01-01')"))
            conn.execute(text("INSERT INTO codigos VALUES (1, '7891234567890')"))
            conn.commit()

        # Act
        products = source.get_all_products()

        # Assert
        assert len(products) == 1
        p = products[0]
        assert p.internal_code == '123'
        assert p.name == 'Produto Teste'
        assert p.sale_price == Decimal('10.50')
        assert p.cost_price == Decimal('5.00')
        assert p.stock == 100.0
        assert p.group == 'GRUPO A'
        assert p.family == 'FAMILIA X'
        assert p.is_active is True
        assert p.barcodes == ['7891234567890']

    def test_produto_inativo(self, engine, source):
        """Produto com stdetalheativo=0 deve ter is_active=False."""
        # Arrange
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO detalhe
                VALUES ('999', 'Inativo', 20.0, 10.0, 0, 1, 1, 1)
            """))
            conn.execute(text("INSERT INTO produto VALUES (1, 1)"))
            conn.execute(text("INSERT INTO grupo VALUES (1, 'GRUPO')"))
            conn.execute(text("INSERT INTO familia VALUES (1, 'FAMILIA')"))
            conn.execute(text("INSERT INTO estoque VALUES (1, 50.0, '2026-01-01')"))
            conn.commit()

        # Act
        products = source.get_all_products()

        # Assert
        assert len(products) == 1
        assert products[0].is_active is False
        assert products[0].internal_code == '999'

    def test_multiplos_codigos_de_barras(self, engine, source):
        """Produto com 2 códigos de barras deve retornar ambos."""
        # Arrange
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO detalhe
                VALUES ('456', 'Multi Barcode', 15.0, 7.0, 1, 1, 1, 1)
            """))
            conn.execute(text("INSERT INTO produto VALUES (1, 1)"))
            conn.execute(text("INSERT INTO grupo VALUES (1, 'GRUPO')"))
            conn.execute(text("INSERT INTO familia VALUES (1, 'FAMILIA')"))
            conn.execute(text("INSERT INTO estoque VALUES (1, 30.0, '2026-01-01')"))
            conn.execute(text("INSERT INTO codigos VALUES (1, '7891111111111')"))
            conn.execute(text("INSERT INTO codigos VALUES (1, '7892222222222')"))
            conn.commit()

        # Act
        products = source.get_all_products()

        # Assert
        assert len(products) == 1
        p = products[0]
        assert p.internal_code == '456'
        assert len(p.barcodes) == 2
        assert '7891111111111' in p.barcodes
        assert '7892222222222' in p.barcodes

    def test_grupo_familia_vazios(self, engine, source):
        """Sem grupo/familia, deve retornar 'SEM GRUPO'/'SEM FAMILIA'."""
        # Arrange — insere sem JOIN em grupo/familia
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO detalhe
                VALUES ('777', 'Sem Grupo', 8.0, 3.0, 1, NULL, 1, 1)
            """))
            # produto sem grupo
            conn.execute(text("INSERT INTO produto VALUES (1, NULL)"))
            conn.execute(text("INSERT INTO grupo VALUES (99, 'OUTRO GRUPO')"))
            # familia sem correspondencia
            conn.execute(text("INSERT INTO familia VALUES (99, 'OUTRA FAMILIA')"))
            conn.execute(text("INSERT INTO estoque VALUES (1, 10.0, '2026-01-01')"))
            conn.commit()

        # Act
        products = source.get_all_products()

        # Assert
        assert len(products) == 1
        p = products[0]
        assert p.group == 'SEM GRUPO'
        assert p.family == 'SEM FAMILIA'

    def test_estoque_zero_retorna_zero(self, engine, source):
        """Produto sem estoque deve retornar stock=0.0."""
        # Arrange — insere detalhe sem registro em estoque
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO detalhe
                VALUES ('888', 'Sem Estoque', 12.0, 6.0, 1, 1, 1, 1)
            """))
            conn.execute(text("INSERT INTO produto VALUES (1, 1)"))
            conn.execute(text("INSERT INTO grupo VALUES (1, 'GRUPO')"))
            conn.execute(text("INSERT INTO familia VALUES (1, 'FAMILIA')"))
            # Não insere estoque — LEFT JOIN vai produzir NULL
            conn.commit()

        # Act
        products = source.get_all_products()

        # Assert
        assert len(products) == 1
        assert products[0].stock == 0.0  # NULL mapeado como 0.0 via COALESCE nao tem; mas float(None) no Python?

    def test_lista_vazia_quando_sem_dados(self, source):
        """Sem nenhum registro no banco, retorna lista vazia."""
        products = source.get_all_products()
        assert products == []

    def test_produto_sem_codigos_de_barras(self, engine, source):
        """Produto sem códigos de barras deve retornar barcodes vazio."""
        # Arrange
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO detalhe
                VALUES ('AAA', 'Sem Codigo', 5.0, 2.0, 1, 1, 1, 1)
            """))
            conn.execute(text("INSERT INTO produto VALUES (1, 1)"))
            conn.execute(text("INSERT INTO grupo VALUES (1, 'GRUPO')"))
            conn.execute(text("INSERT INTO familia VALUES (1, 'FAMILIA')"))
            conn.execute(text("INSERT INTO estoque VALUES (1, 20.0, '2026-01-01')"))
            # Sem insert em codigos
            conn.commit()

        # Act
        products = source.get_all_products()

        # Assert
        assert len(products) == 1
        assert products[0].barcodes == []
