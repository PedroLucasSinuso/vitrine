from abc import ABC, abstractmethod
from datetime import date

from vitrine_core.datasets.agregacao import atendimentos_da_loja, vendas_diarias, vendedor_periodo
from vitrine_core.datasets.conversao import itens_de_transacoes
from vitrine_core.datasets.tipos import ItemVenda, TipoDataset, VendaDiaria, VendaVendedorPeriodo
from vitrine_core.interfaces.source import TransactionSource


class FonteEquipe(ABC):
    tipos: set[TipoDataset]

    @abstractmethod
    def vendedor_periodo(self, inicio: date, fim: date) -> list[VendaVendedorPeriodo]: ...

    def atendimentos_loja(self, inicio: date, fim: date) -> int | None:
        return None

    def diarias(self, inicio: date, fim: date) -> list[VendaDiaria] | None:
        return None

    def itens(self, inicio: date, fim: date) -> list[ItemVenda] | None:
        return None


class FonteEquipeErp(FonteEquipe):
    tipos = {TipoDataset.ITENS_VENDA}

    def __init__(self, source: TransactionSource):
        self._source = source

    def itens(self, inicio: date, fim: date) -> list[ItemVenda]:
        return itens_de_transacoes(self._source.get_items(inicio, fim))

    def vendedor_periodo(self, inicio: date, fim: date) -> list[VendaVendedorPeriodo]:
        return vendedor_periodo(self.itens(inicio, fim), inicio, fim)

    def atendimentos_loja(self, inicio: date, fim: date) -> int:
        return atendimentos_da_loja(self.itens(inicio, fim))

    def diarias(self, inicio: date, fim: date) -> list[VendaDiaria]:
        return vendas_diarias(self.itens(inicio, fim))
