"""Adapter de demonstração — dados sintéticos, sem ERP nenhum.

Existe para o Vitrine poder ser mostrado (portfólio, avaliação, testes de
ponta a ponta) sem depender do banco de um cliente real. Uma empresa passa
a usá-lo com a configuração ``erp_adapter="demo"``.

Nada aqui toca banco de dados externo: as fábricas ignoram a sessão e o
``empresa_id`` que recebem, porque o conteúdo é o mesmo para qualquer
tenant que aponte para a demo.
"""

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from app.application.adapter_registry import AdapterEntry
from app.core.interfaces.source import ProductSource, TransactionSource


def _criar_product_source(db: Session, empresa_id: int) -> ProductSource:
    from app.adapters.demo.product_source import DemoProductSource

    return DemoProductSource()


def _criar_transaction_source(db: Session, empresa_id: int) -> TransactionSource:
    from app.adapters.demo.transaction_source import DemoTransactionSource

    return DemoTransactionSource()


@contextmanager
def _abrir_sync_source(
    db: Session, empresa_id: int, pool_size: int = 1
) -> Iterator[ProductSource]:
    """Sem conexão para abrir nem recurso para descartar."""
    from app.adapters.demo.product_source import DemoProductSource

    yield DemoProductSource()


ENTRY = AdapterEntry(
    nome="demo",
    criar_product_source=_criar_product_source,
    criar_transaction_source=_criar_transaction_source,
    abrir_sync_source=_abrir_sync_source,
)
