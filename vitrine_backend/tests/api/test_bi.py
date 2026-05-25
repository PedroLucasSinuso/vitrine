"""Tests for BI endpoints — Tabela de Preços / Tabela Produtos."""

import pytest


def test_tabela_produtos_shape(client, db_session, token_admin):
    """Verifica shape da resposta de /bi/tabela-produtos."""
    from app.domain.models.produto import Produto

    # Arrange: cria um produto
    p = Produto(
        codigo_chamada="001",
        nome="Produto Teste",
        grupo="ALIMENTOS",
        familia="BEBIDAS",
        preco_venda=100.0,
        preco_custo=60.0,
        estoque=10.0,
    )
    db_session.add(p)
    db_session.commit()

    # Act
    headers = {"Authorization": f"Bearer {token_admin}"}
    resp = client.get("/bi/tabela-produtos", headers=headers)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["codigo_chamada"] == "001"
    assert item["nome"] == "Produto Teste"
    assert item["grupo"] == "ALIMENTOS"
    assert item["familia"] == "BEBIDAS"
    assert item["preco_venda"] == 100.0
    assert item["preco_custo"] == 60.0
    assert item["markup"] == pytest.approx(66.67, rel=0.1)  # (100-60)/60 * 100
    assert item["margem"] == pytest.approx(40.0, rel=0.1)   # (100-60)/100 * 100
    assert item["estoque"] == 10.0
    assert "filtros_disponiveis" in data
    assert "grupos" in data["filtros_disponiveis"]
    assert "familias" in data["filtros_disponiveis"]
