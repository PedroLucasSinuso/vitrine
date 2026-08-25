"""Adapter do ERP Alterdata (PostgreSQL).

Expõe ``ENTRY``, que é como o resto do sistema constrói as fontes de dados
deste ERP — ver ``app/application/adapter_registry.py``.

Todas as fábricas recebem ``empresa_id`` porque cada empresa tem o seu
próprio Alterdata (host/base/credenciais diferentes): é o que garante que
o sync ou a consulta de uma empresa nunca leia o ERP de outra.
"""

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from app.application.adapter_registry import AdapterEntry
from app.core.interfaces.source import ProductSource, TransactionSource


def _criar_product_source(db: Session, empresa_id: int) -> ProductSource:
    from app.adapters.alterdata.db import get_alterdata_engine
    from app.adapters.alterdata.product_source import AlterdataProductSource

    return AlterdataProductSource(get_alterdata_engine(db, empresa_id))


def _criar_transaction_source(db: Session, empresa_id: int) -> TransactionSource:
    from app.adapters.alterdata.db import get_alterdata_engine
    from app.adapters.alterdata.transaction_source import AlterdataTransactionSource

    return AlterdataTransactionSource(get_alterdata_engine(db, empresa_id))


@contextmanager
def _abrir_sync_source(
    db: Session, empresa_id: int, pool_size: int = 1
) -> Iterator[ProductSource]:
    """Entrega o ProductSource do sync e descarta o engine ao final.

    O sync usa um engine próprio (pool pequeno) que precisa ser descartado
    mesmo quando o sync falha — daí o try/finally.
    """
    from app.adapters.alterdata.db import get_alterdata_engine
    from app.adapters.alterdata.product_source import AlterdataProductSource

    engine = get_alterdata_engine(db, empresa_id, pool_size=pool_size)
    try:
        yield AlterdataProductSource(engine)
    finally:
        engine.dispose()


def _ao_terminar_sync() -> None:
    from app.adapters.alterdata.transaction_source import invalidar_cache_transacoes

    invalidar_cache_transacoes()


ENTRY = AdapterEntry(
    nome="alterdata",
    criar_product_source=_criar_product_source,
    criar_transaction_source=_criar_transaction_source,
    abrir_sync_source=_abrir_sync_source,
    ao_terminar_sync=_ao_terminar_sync,
)
