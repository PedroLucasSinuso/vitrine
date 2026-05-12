import pytest
from unittest.mock import Mock
from app.domain.models.produto import Produto
from app.application.services.produto_service import ProdutoService

# Fixtures
@pytest.fixture
def produto():
    return Produto(
        codigo_chamada="000123",
        nome="Teste",
        grupo="Grupo",
        familia="Familia",
        preco_custo=10,
        preco_venda=15,
        estoque=10,
        codigos=[],
    )

@pytest.fixture
def repo_mock(produto):
    repo = Mock()
    repo.obter_por_codigo.return_value = produto
    repo.listar_paginado.return_value = []
    return repo

def test_obter_por_codigo_retorna_produto(repo_mock, produto):
    service = ProdutoService(repo_mock)

    result = service.obter_por_codigo("000123")

    assert result is produto

def test_obter_por_codigo_produto_nao_encontrado(repo_mock):
    repo_mock.obter_por_codigo.return_value = None

    service = ProdutoService(repo_mock)

    result = service.obter_por_codigo("000123")

    assert result is None
    
# listar_paginado
@pytest.mark.parametrize("limit_entrada, limit_esperado", [
    (200, 100),
    (0, 1),
    (50, 50),
])
def test_listar_paginado_clamp(repo_mock, limit_entrada, limit_esperado):
    service = ProdutoService(repo_mock)

    service.listar_paginado(limit=limit_entrada, offset=5)

    repo_mock.listar_paginado.assert_called_once_with(limit_esperado, 5)