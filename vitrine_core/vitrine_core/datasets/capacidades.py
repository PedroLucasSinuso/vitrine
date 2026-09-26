from vitrine_core.datasets.tipos import TipoDataset

FORNECE: dict[TipoDataset, set[TipoDataset]] = {
    TipoDataset.ITENS_VENDA: {
        TipoDataset.ITENS_VENDA,
        TipoDataset.VENDAS_DIARIAS,
        TipoDataset.VENDAS_VENDEDOR_PERIODO,
        TipoDataset.VENDAS_PRODUTO_PERIODO,
    },
    TipoDataset.VENDAS_DIARIAS: {TipoDataset.VENDAS_DIARIAS, TipoDataset.VENDAS_VENDEDOR_PERIODO},
    TipoDataset.VENDAS_VENDEDOR_PERIODO: {TipoDataset.VENDAS_VENDEDOR_PERIODO},
    TipoDataset.VENDAS_PRODUTO_PERIODO: {TipoDataset.VENDAS_PRODUTO_PERIODO},
    TipoDataset.CONTATOS_VENDEDOR: {TipoDataset.CONTATOS_VENDEDOR},
}


def tipos_derivaveis(disponiveis: set[TipoDataset]) -> set[TipoDataset]:
    return set().union(*(FORNECE[t] for t in disponiveis)) if disponiveis else set()
