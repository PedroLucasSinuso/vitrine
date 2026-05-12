import pytest
from pytest import approx
from app.domain.models.produto import Produto, ProdutoCodigo

def criar_produto1():
    return Produto(
        codigo_chamada="000123",
        preco_custo=10.0,
        preco_venda=15.0,
        estoque=100,
        grupo="EletrÃ´nicos",
        familia="Smartphones",
        nome="Smartphone XYZ",
        codigos=[
            ProdutoCodigo(codigo="1234567891234"),
            ProdutoCodigo(codigo_chamada="000123"),
        ]
    )


def criar_produto2():
    return Produto(
        codigo_chamada="000124",
        preco_custo=0.0,
        preco_venda=0.0,
        estoque=50,
        grupo="EletrÃ´nicos",
        familia="Tablets",
        nome="Tablet ABC",
        codigos=[
            ProdutoCodigo(codigo="9876543219876"),
            ProdutoCodigo(codigo="000124"),
        ]
    )

def criar_produto3():
    return Produto(
        codigo_chamada="000124",
        preco_custo=0.0,
        preco_venda=0.0,
        estoque=50,
        grupo="EletrÃ´nicos",
        familia="Tablets",
        nome="Tablet ABC",
        codigos=[]
    )

# Estrutura bÃ¡sica
@pytest.mark.parametrize("produto", [criar_produto1(), criar_produto2()])
def test_produto_codigos(produto):
    assert len(produto.codigos) == 2

def test_produto_sem_codigos():
    produto = criar_produto3()
    assert len(produto.codigos) == 0

# Produto com margem
def test_metricas_produto_com_margem():
    produto = criar_produto1()

    assert produto.markup == approx(0.5, abs=0.01)
    assert produto.margem == approx(0.33, abs=0.01)

# Produto sem custo (edge case)
def test_metricas_produto_sem_custo():
    produto = criar_produto2()

    assert produto.markup == 0.0
    assert produto.margem == 0.0