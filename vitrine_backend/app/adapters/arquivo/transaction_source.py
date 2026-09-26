from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.importacao import Dataset, DsItemVenda
from vitrine_core.datasets.tipos import Operacao, TipoDataset
from vitrine_core.interfaces.source import TransactionSource
from vitrine_core.models.transaction import OperationType, TransactionItem

_OPERACOES = {Operacao.VENDA.value: OperationType.SALE, Operacao.TROCA.value: OperationType.RETURN}


class DatasetTransactionSource(TransactionSource):
    def __init__(self, db: Session, empresa_id: int):
        self._db = db
        self._empresa_id = empresa_id

    def _datasets(self, start: date, end: date) -> list[int]:
        datasets = self._db.scalars(
            select(Dataset)
            .where(
                Dataset.empresa_id == self._empresa_id,
                Dataset.tipo == TipoDataset.ITENS_VENDA.value,
                Dataset.inicio <= end,
                Dataset.fim >= start,
            )
            .order_by(Dataset.criado_em.desc(), Dataset.id.desc())
        )
        escolhidos: list[Dataset] = []
        for dataset in datasets:
            if not any(dataset.inicio <= e.fim and e.inicio <= dataset.fim for e in escolhidos):
                escolhidos.append(dataset)
        return [d.id for d in escolhidos]

    def get_items(self, start: date, end: date) -> list[TransactionItem]:
        ids = self._datasets(start, end)
        if not ids:
            return []
        linhas = list(self._db.scalars(
            select(DsItemVenda)
            .where(DsItemVenda.dataset_id.in_(ids), DsItemVenda.data >= start, DsItemVenda.data <= end)
            .order_by(DsItemVenda.id)
        ))
        totais: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for linha in linhas:
            sinal = -1 if linha.operacao == Operacao.TROCA.value else 1
            totais[linha.documento] += sinal * linha.valor
        return [
            TransactionItem(
                document_id=linha.documento,
                date=linha.data,
                time=linha.hora,
                operation=_OPERACOES[linha.operacao],
                product_code=linha.codigo_produto or linha.produto,
                product_name=linha.produto,
                group_name=linha.grupo,
                family_name=linha.familia,
                quantity=linha.quantidade,
                line_total=linha.valor if linha.operacao == Operacao.VENDA.value else -linha.valor,
                document_total=totais[linha.documento],
            )
            for linha in linhas
        ]
