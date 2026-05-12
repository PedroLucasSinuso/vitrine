from pytest import approx
from app.domain.models.produto import Produto
from app.schemas.produto_schema import ProdutoResponse

class FakeProduto:
    def __init__(self):
        self.codigo_chamada = "000123"
        self.grupo = "Eletrônicos"
        self.familia = "Smartphones"
        self.nome = "Produto X"
        self.preco_venda = 10.0
        self.preco_custo = 5.0
        self.estoque = 20
        self.markup = 1.0
        self.margem = 0.5

def criar_produto():
    return Produto(
        codigo_chamada="000123",
        nome="Teste",
        grupo="Grupo",
        familia="Familia",
        preco_custo=10,
        preco_venda=15,
        estoque=10
    )

#Teste de serialização direta a partir de um objeto ORM
def test_produto_response():
    produto = criar_produto()

    response = ProdutoResponse.model_validate(produto)

    assert response.codigo_chamada == "000123"
    assert response.nome == "Teste"
    assert response.grupo == "Grupo"
    assert response.familia == "Familia"
    assert response.preco_custo == 10
    assert response.preco_venda == 15
    assert response.estoque == 10
    assert response.markup == approx(0.5, abs=0.01)
    assert response.margem == approx(0.33, abs=0.01)
    assert response.codigo_buscado is None

# Teste de serialização direta a partir de um objeto não ORM
def test_model_validade_from_atributes():
    fake_produto = FakeProduto()

    response = ProdutoResponse.model_validate(fake_produto)

    assert response.codigo_chamada == "000123"
    assert response.nome == "Produto X"
    assert response.grupo == "Eletrônicos"
    assert response.familia == "Smartphones"
    assert response.preco_custo == 5.0
    assert response.preco_venda == 10.0
    assert response.estoque == 20
    assert response.markup == approx(1.0, abs=0.01)
    assert response.margem == approx(0.5, abs=0.01)
    assert response.codigo_buscado is None

# Test codigo_buscado preenchido corretamente a partir do endpoint, sem precisar de um produto real
def test_model_codigo_buscado():
    produto = criar_produto()
    response = ProdutoResponse.model_validate(produto)
    response.codigo_buscado = "000123"
    assert response.codigo_buscado == "000123"