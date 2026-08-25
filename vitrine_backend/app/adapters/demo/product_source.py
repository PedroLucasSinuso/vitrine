"""Fonte de produtos da demonstração."""

from datetime import date

from app.adapters.demo.catalog import CATALOGO
from app.adapters.demo.pricing import ativo, custo_no_dia, estoque_no_dia, preco_no_dia
from app.core.interfaces.source import ProductSource
from app.core.models.product import Product


class DemoProductSource(ProductSource):
    """Catálogo sintético, com preço e estoque do dia da consulta.

    Preço e custo saem das mesmas funções que o gerador de transações usa —
    é o que mantém a tabela de preços coerente com a receita do BI.

    Como o preço deriva de mês a mês, cada sincronização registra um ponto
    novo no histórico de preços, e o gráfico de evolução se preenche
    sozinho ao longo do tempo.
    """

    def get_all_products(self) -> list[Product]:
        hoje = date.today()
        return [
            Product(
                internal_code=sku.internal_code,
                name=sku.nome,
                # O código interno entra junto dos EANs porque é assim que o
                # ERP real devolve: a consulta por PLU do balcão passa pela
                # mesma tabela de códigos que a leitura do código de barras.
                barcodes=[sku.internal_code, *sku.barcodes],
                sale_price=preco_no_dia(sku, hoje),
                cost_price=custo_no_dia(sku, hoje),
                stock=estoque_no_dia(sku, hoje),
                group=sku.grupo,
                family=sku.familia,
                is_active=ativo(sku),
            )
            for sku in CATALOGO
        ]
