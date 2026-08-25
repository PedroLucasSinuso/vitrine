"""Criação das fontes de dados do ERP de uma empresa.

Camada fina entre quem precisa dos dados (rotas, sync, schedulers) e o
adapter concreto do ERP daquela empresa. Nada aqui conhece Alterdata ou
qualquer outro ERP: o adapter é resolvido em tempo de execução pela
configuração ``erp_adapter`` da empresa, via
``app/application/adapter_registry.py``.

Multi-tenant: toda função recebe ``empresa_id`` e o repassa até o adapter —
é isso que garante que o sync/consulta de uma empresa nunca leia o ERP de
outra.
"""

from sqlalchemy.orm import Session

from app.application.adapter_registry import get_adapter
from app.core.interfaces.source import ProductSource, TransactionSource

ADAPTER_PADRAO = "alterdata"


def nome_adapter(db: Session, empresa_id: int) -> str:
    """Nome do ERP configurado para a empresa (ex: 'alterdata', 'demo')."""
    from app.application.config_service import get as get_config

    return get_config(db, empresa_id, "erp_adapter", ADAPTER_PADRAO)


def create_product_source(db: Session, empresa_id: int) -> ProductSource:
    return get_adapter(nome_adapter(db, empresa_id)).criar_product_source(db, empresa_id)


def create_transaction_source(db: Session, empresa_id: int) -> TransactionSource:
    return get_adapter(nome_adapter(db, empresa_id)).criar_transaction_source(db, empresa_id)


def run_sync_common(
    session: Session,
    empresa_id: int,
    job_id: str | None = None,
    pool_size: int = 1,
    invalidate_cache: bool = True,
) -> object | None:
    """Executa o sync DE UMA EMPRESA com lifecycle seguro.

    Abre a fonte de produtos do ERP daquela empresa (o adapter cuida de
    descartar o que for caro na saída), roda o SyncService escopado a ela e
    deixa o adapter invalidar os próprios caches.

    O caller é responsável por:
    - init_db() / criação da sessão
    - Gerenciamento do SyncJob (status, started_at, etc.)
    - session.close()
    """
    from app.application.sync_service import SyncService

    entry = get_adapter(nome_adapter(session, empresa_id))
    with entry.abrir_sync_source(session, empresa_id, pool_size) as source:
        result = SyncService(source, session, empresa_id=empresa_id).sync(job_id=job_id)
    if invalidate_cache:
        entry.ao_terminar_sync()
    return result
