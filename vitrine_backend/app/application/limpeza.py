import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.domain.models.cache_status import CacheStatus
from app.domain.models.sync_job import SyncJob
from app.domain.models.tentativa_login import TentativaLogin
from app.domain.models.token_blacklist import TokenBlacklist

logger = logging.getLogger(__name__)

JOB_ID_LIMPEZA = "limpeza_registros_antigos"
RETENCAO_TENTATIVAS_LOGIN = timedelta(days=30)
RETENCAO_SYNC_JOBS = timedelta(days=90)
RETENCAO_CACHE_STATUS = timedelta(days=30)


@dataclass(frozen=True)
class ResultadoLimpeza:
    tokens: int
    tentativas_login: int
    sync_jobs: int
    cache_status: int


def limpar_registros_antigos(session: Session, agora: datetime | None = None) -> ResultadoLimpeza:
    agora = agora or datetime.now(timezone.utc)

    tokens = session.execute(
        delete(TokenBlacklist).where(TokenBlacklist.expires_at < agora)
    ).rowcount
    tentativas = session.execute(
        delete(TentativaLogin).where(TentativaLogin.attempted_at < agora - RETENCAO_TENTATIVAS_LOGIN)
    ).rowcount
    jobs = session.execute(
        delete(SyncJob).where(SyncJob.finished_at < agora - RETENCAO_SYNC_JOBS)
    ).rowcount

    mais_recente_por_empresa = select(func.max(CacheStatus.id)).group_by(CacheStatus.empresa_id)
    cache = session.execute(
        delete(CacheStatus).where(
            CacheStatus.last_updated < agora - RETENCAO_CACHE_STATUS,
            CacheStatus.id.not_in(mais_recente_por_empresa.scalar_subquery()),
        )
    ).rowcount

    session.commit()
    resultado = ResultadoLimpeza(tokens, tentativas, jobs, cache)
    logger.info("Limpeza de registros antigos | %s", resultado)
    return resultado


def _executar_limpeza() -> None:
    from app.infrastructure.db.session import SessionLocal

    try:
        with SessionLocal() as session:
            limpar_registros_antigos(session)
    except Exception:
        logger.exception("Falha na limpeza de registros antigos")


def agendar_limpeza(scheduler) -> None:
    scheduler.add_job(
        _executar_limpeza,
        trigger="cron",
        hour=3,
        minute=30,
        id=JOB_ID_LIMPEZA,
        replace_existing=True,
        misfire_grace_time=3600,
    )
