"""Factory functions for ERP adapters.

Centraliza a criação de objetos do adapter Alterdata (ProductSource,
TransactionSource, engine) para evitar que detalhes de implementação do
adapter vazem para camadas superiores (api, application).

Multi-tenant: cada empresa tem seu próprio ERP (host/db/credenciais
diferentes), então toda função aqui recebe ``empresa_id`` e o repassa até
``get_alterdata_engine`` — é isso que garante que o sync/consulta de uma
empresa nunca acidentalmente lê o ERP de outra.
"""

from sqlalchemy.orm import Session
from app.core.interfaces.source import ProductSource, TransactionSource


def create_product_source(db: Session, empresa_id: int) -> ProductSource:
    from app.adapters.alterdata.product_source import AlterdataProductSource
    from app.adapters.alterdata.db import get_alterdata_engine

    return AlterdataProductSource(get_alterdata_engine(db, empresa_id))


def create_transaction_source(db: Session, empresa_id: int) -> TransactionSource:
    from app.adapters.alterdata.transaction_source import AlterdataTransactionSource
    from app.adapters.alterdata.db import get_alterdata_engine

    return AlterdataTransactionSource(get_alterdata_engine(db, empresa_id))


def create_sync_engine_and_source(
    db: Session, empresa_id: int, pool_size: int = 1
) -> tuple[object, ProductSource]:
    """Cria engine e ProductSource para sync.

    Retorna (engine, source) para que o caller possa descartar o engine
    no finally.
    """
    from app.adapters.alterdata.product_source import AlterdataProductSource
    from app.adapters.alterdata.db import get_alterdata_engine

    engine = get_alterdata_engine(db, empresa_id, pool_size=pool_size)
    source = AlterdataProductSource(engine)
    return engine, source


def run_sync_common(
    session: Session,
    empresa_id: int,
    job_id: str | None = None,
    pool_size: int = 1,
    invalidate_cache: bool = True,
) -> object | None:
    """Executa o sync (engine + service) DE UMA EMPRESA com lifecycle seguro.

    Cria engine PostgreSQL (do ERP daquela empresa), instancia SyncService
    escopado a ela, executa sync, invalida cache de transações (opcional)
    e descarta o engine.

    O caller é responsável por:
    - init_db() / criação da sessão
    - Gerenciamento do SyncJob (status, started_at, etc.)
    - session.close()
    """
    from app.adapters.alterdata.db import get_alterdata_engine
    from app.adapters.alterdata.product_source import AlterdataProductSource
    from app.application.sync_service import SyncService
    from app.adapters.alterdata.transaction_source import invalidar_cache_transacoes

    engine = None
    try:
        engine = get_alterdata_engine(session, empresa_id, pool_size=pool_size)
        source = AlterdataProductSource(engine)
        service = SyncService(source, session, empresa_id=empresa_id)
        result = service.sync(job_id=job_id)
        if invalidate_cache:
            invalidar_cache_transacoes()
        return result
    except Exception:
        raise
    finally:
        if engine is not None:
            engine.dispose()
