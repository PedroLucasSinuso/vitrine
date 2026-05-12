from app.application.etl.dto import ProdutoRow, CodigoRow
from app.application.etl.transform.transformer import transformar_produtos


def test_transformar_produtos():
    produtos_rows = [
        ProdutoRow(
            codigo_chamada="000123",
            nome="Teste",
            grupo="Grupo",
            familia="Familia",
            preco_custo=10,
            preco_venda=15,
           estoque=10
        )
    ]

    codigos_rows = [
        CodigoRow(codigo_chamada="000123", codigo="ABC123"),
        CodigoRow(codigo_chamada="000123", codigo="DEF456")
    ]

    produtos = transformar_produtos(produtos_rows, codigos_rows)

    assert len(produtos) == 1
    produto = produtos[0]
    assert produto.codigo_chamada == "000123"
    assert produto.nome == "Teste"
    assert len(produto.codigos) == 2
    produto_codigos = [codigo.codigo for codigo in produto.codigos]
    assert "ABC123" in produto_codigos
    assert "DEF456" in produto_codigos