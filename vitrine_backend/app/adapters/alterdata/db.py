import threading
import time

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from app.application.config_service import montar_url_postgres


# Cache de engines PostgreSQL para evitar recriação a cada request.
# A chave inclui a URL + pool_size para que sync (pool_size=1) e
# BI (pool_size=2) tenham entries separadas.
# O TTL de 1h equilibra frescor (refletir mudanças de config) com
# reaproveitamento de pool de conexões.
_engine_cache: dict[str, tuple[Engine, float]] = {}
_engine_cache_lock = threading.Lock()
_ENGINE_CACHE_TTL = 3600  # 1 hora


def _make_cache_key(url: str, pool_size: int) -> str:
    return f"{url}::pool{pool_size}"


def get_alterdata_engine(db: Session, empresa_id: int, pool_size: int = 2) -> Engine:
    """Retorna um engine SQLAlchemy para o PostgreSQL do Alterdata DA EMPRESA.

    A URL de conexão é montada dinamicamente a partir das configurações
    de ERP DAQUELA EMPRESA (armazenadas no SQLite — erp_host, erp_port,
    etc.) via montar_url_postgres(). Cada empresa tem seu próprio ERP,
    então a URL — e portanto o engine cacheado — é sempre por tenant
    (a chave do cache já inclui a URL inteira, que já embute o host/db/
    usuário daquela empresa, então não há risco de um tenant reusar o
    pool de conexão de outro).

    O engine é cacheado em memória por até 1h (chave = url + pool_size)
    para evitar recriação do pool de conexões a cada request. Se a config
    do ERP for alterada, o cache expira em no máximo 1h.

    Args:
        db: Sessão SQLAlchemy para ler config do ERP.
        empresa_id: tenant cujo ERP será conectado.
        pool_size: Tamanho do pool de conexões. Sync usa pool_size=1
                   para não disputar conexões com BI (C2).
    """
    url = montar_url_postgres(db, empresa_id)
    if not url:
        raise RuntimeError(
            "ERP não configurado. "
            "Acesse Admin > Configurações > ERP para configurar os campos "
            "de conexão (host, porta, database, usuário e senha)."
        )

    now = time.time()

    # Sync (pool_size=1) não é cacheado porque run_sync_common() sempre
    # chama engine.dispose() no finally. Apenas pools compartilhados
    # (BI/Product, pool_size >= 2) são cacheados para reaproveitar conexões.
    if pool_size > 1:
        key = _make_cache_key(url, pool_size)
        with _engine_cache_lock:
            if key in _engine_cache:
                engine, ts = _engine_cache[key]
                if now - ts < _ENGINE_CACHE_TTL:
                    return engine

    engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=1,
        connect_args={"connect_timeout": 10},
    )

    if pool_size > 1:
        with _engine_cache_lock:
            _engine_cache[key] = (engine, now)

    return engine
