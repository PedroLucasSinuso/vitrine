from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import date

from vitrine_core.datasets.agregacao import (
    atendimentos_da_loja,
    vendas_diarias,
    vendedor_periodo,
    vendedor_periodo_de_diarias,
)
from vitrine_core.datasets.conversao import itens_de_transacoes
from vitrine_core.datasets.tipos import ContatoVendedor, ItemVenda, TipoDataset, VendaDiaria, VendaVendedorPeriodo
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

    def contatos(self, inicio: date, fim: date) -> list[ContatoVendedor] | None:
        return None


class FonteEquipeErp(FonteEquipe):
    tipos = {TipoDataset.ITENS_VENDA}

    def __init__(self, source: TransactionSource | Callable[[], TransactionSource]):
        self._source = source

    def _fonte(self) -> TransactionSource:
        if callable(self._source) and not isinstance(self._source, TransactionSource):
            self._source = self._source()
        return self._source

    def itens(self, inicio: date, fim: date) -> list[ItemVenda]:
        return itens_de_transacoes(self._fonte().get_items(inicio, fim))

    def vendedor_periodo(self, inicio: date, fim: date) -> list[VendaVendedorPeriodo]:
        return vendedor_periodo(self.itens(inicio, fim), inicio, fim)

    def atendimentos_loja(self, inicio: date, fim: date) -> int:
        return atendimentos_da_loja(self.itens(inicio, fim))

    def diarias(self, inicio: date, fim: date) -> list[VendaDiaria]:
        return vendas_diarias(self.itens(inicio, fim))


class FonteEquipeDatasets(FonteEquipe):
    def __init__(self, db, empresa_id: int):
        from app.application.importacao.persistencia import datasets_da_empresa

        self._db = db
        self._datasets = datasets_da_empresa(db, empresa_id)
        self.tipos = {TipoDataset(d.tipo) for d in self._datasets}

    def _mais_recentes_sem_sobreposicao(self, tipo: TipoDataset, inicio: date, fim: date, contidos: bool):
        escolhidos = []
        for dataset in self._datasets:
            if dataset.tipo != tipo.value:
                continue
            dentro = inicio <= dataset.inicio and dataset.fim <= fim
            cruza = dataset.inicio <= fim and inicio <= dataset.fim
            if not (dentro if contidos else cruza):
                continue
            if any(dataset.inicio <= e.fim and e.inicio <= dataset.fim for e in escolhidos):
                continue
            escolhidos.append(dataset)
        return escolhidos

    def _linhas(self, tipo: TipoDataset, inicio: date, fim: date, contidos: bool) -> list:
        from app.application.importacao.persistencia import linhas_do_dataset

        linhas = []
        for dataset in self._mais_recentes_sem_sobreposicao(tipo, inicio, fim, contidos):
            linhas.extend(linhas_do_dataset(self._db, dataset))
        return linhas

    def itens(self, inicio: date, fim: date) -> list[ItemVenda] | None:
        if TipoDataset.ITENS_VENDA not in self.tipos:
            return None
        return [i for i in self._linhas(TipoDataset.ITENS_VENDA, inicio, fim, contidos=False) if inicio <= i.data <= fim]

    def diarias(self, inicio: date, fim: date) -> list[VendaDiaria] | None:
        itens = self.itens(inicio, fim)
        if itens is not None:
            return vendas_diarias(itens)
        if TipoDataset.VENDAS_DIARIAS not in self.tipos:
            return None
        return [d for d in self._linhas(TipoDataset.VENDAS_DIARIAS, inicio, fim, contidos=False) if inicio <= d.data <= fim]

    def vendedor_periodo(self, inicio: date, fim: date) -> list[VendaVendedorPeriodo]:
        itens = self.itens(inicio, fim)
        if itens is not None:
            return vendedor_periodo(itens, inicio, fim)
        por_periodo = self._linhas(TipoDataset.VENDAS_VENDEDOR_PERIODO, inicio, fim, contidos=True)
        if por_periodo:
            return por_periodo
        diarias = self.diarias(inicio, fim)
        return vendedor_periodo_de_diarias(diarias, inicio, fim) if diarias else []

    def atendimentos_loja(self, inicio: date, fim: date) -> int | None:
        itens = self.itens(inicio, fim)
        return atendimentos_da_loja(itens) if itens is not None else None

    def contatos(self, inicio: date, fim: date) -> list[ContatoVendedor] | None:
        if TipoDataset.CONTATOS_VENDEDOR not in self.tipos:
            return None
        return self._linhas(TipoDataset.CONTATOS_VENDEDOR, inicio, fim, contidos=True)
