import uuid
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.schemas.sync_schema import (
    SyncStatusResponse,
    SyncTriggerResponse,
    SyncListResponse,
)
from app.domain.models.sync_job import SyncJob
from app.domain.models.usuario import Usuario
from app.core.error_handler import sanitizar_erro, logar_erro_interno
from app.application.scheduler_manager import listar_jobs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

executor = ThreadPoolExecutor(max_workers=1)


def _run_sync_background(job_id: str):
    from app.infrastructure.db.bootstrap import init_db
    from app.infrastructure.db.session import SqliteSession
    from app.application.erp_factory import run_sync_common
    from app.application.triggers_pos_sync import (
        verificar_margem_negativa,
        verificar_erro_sync,
    )

    init_db()
    session = SqliteSession()

    try:
        job = session.query(SyncJob).filter(SyncJob.job_id == job_id).first()
        if not job:
            logger.error("SyncJob %s not found in DB", job_id)
            return
        job.started_at = datetime.now(timezone.utc)
        job.status = "em_progresso"
        session.commit()
        logger.info("Sync job %s iniciado em background", job_id)

        # run_sync_common cuida de engine, source, service.sync(),
        # invalidação de cache e engine.dispose()
        result = run_sync_common(session, job_id=job_id, pool_size=1)

        if result is None:
            raise RuntimeError("run_sync_common retornou None sem exceção")

        job.status = "sucesso"
        job.finished_at = datetime.now(timezone.utc)
        job.produtos_count = result.produtos_count
        job.codigos_count = result.codigos_count
        session.commit()

        logger.info(
            "Sync job %s concluído | produtos=%s codigos=%s",
            job_id, result.produtos_count, result.codigos_count
        )

        # Triggers pós-sync
        verificar_margem_negativa(session)
        verificar_erro_sync(session)

    except Exception as e:
        session.rollback()
        logar_erro_interno(f"Sync job {job_id} falhou", e)
        try:
            job = session.query(SyncJob).filter(SyncJob.job_id == job_id).first()
            if job:
                job.status = "erro"
                job.finished_at = datetime.now(timezone.utc)
                job.error_message = sanitizar_erro(e)
                session.commit()
        except Exception:
            pass
        # Notificação de erro (sessão pode estar parcial)
        try:
            verificar_erro_sync(session, erro=sanitizar_erro(e))
        except Exception:
            pass
    finally:
        session.close()  # C5: evita vazamento de conexão PostgreSQL


@router.post("/sync", response_model=SyncTriggerResponse, status_code=201)
def trigger_sync(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
):
    job_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc)

    job = SyncJob(
        job_id=job_id,
        status="em_progresso",
        started_at=now,
    )
    db.add(job)
    db.commit()

    executor.submit(_run_sync_background, job_id)

    logger.info("Sync triggered | job_id=%s by admin=%s", job_id, _admin.username)

    return SyncTriggerResponse(
        job_id=job_id,
        status="started",
        message="Sync iniciado em background"
    )


@router.get("/sync/{job_id}", response_model=SyncStatusResponse)
def get_sync_status(
    job_id: str,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
):
    job = db.query(SyncJob).filter(SyncJob.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")

    return SyncStatusResponse(
        job_id=job.job_id,
        started_at=job.started_at,
        finished_at=job.finished_at,
        status=job.status,
        produtos_count=job.produtos_count,
        codigos_count=job.codigos_count,
        error_message=job.error_message,
    )


@router.get("/sync", response_model=SyncListResponse)
def list_sync_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
):
    stmt = (
        select(SyncJob)
        .order_by(SyncJob.id.desc())
        .limit(limit)
    )
    results = db.execute(stmt).scalars().all()

    jobs = [
        SyncStatusResponse(
            job_id=job.job_id,
            started_at=job.started_at,
            finished_at=job.finished_at,
            status=job.status,
            produtos_count=job.produtos_count,
            codigos_count=job.codigos_count,
            error_message=job.error_message,
        )
        for job in results
    ]

    # total deve refletir o número real de registros, não o limit
    total_count = db.query(SyncJob).count()
    return SyncListResponse(jobs=jobs, total=total_count)


@router.get("/scheduler/jobs")
def get_scheduler_jobs(
    _admin: Usuario = Depends(require_admin),
):
    return {"jobs": listar_jobs()}


@router.get("/health")
def health_check():
    """Health check público — sem auth. Retorna status básico do servidor."""
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "vitrine-backend",
    }


@router.get("/scheduler/health")
def get_scheduler_health(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    """Status do scheduler: lock ativo? jobs registrados? heartbeat recente?"""
    from app.domain.models.scheduler_lock import SchedulerLock, STALE_LOCK_MINUTES
    from datetime import datetime, timezone

    lock = db.query(SchedulerLock).filter(SchedulerLock.id == 1).first()
    jobs = listar_jobs()

    lock_status = "ausente"
    if lock:
        idade = (datetime.now(timezone.utc) - lock.heartbeat_at.replace(tzinfo=timezone.utc)).total_seconds()
        lock_status = "ativo" if idade < STALE_LOCK_MINUTES * 60 else "stale"

    return {
        "lock": {
            "status": lock_status,
            "pid": lock.pid if lock else None,
            "hostname": lock.hostname if lock else None,
            "heartbeat_at": lock.heartbeat_at.isoformat() if lock and lock.heartbeat_at else None,
            "stale_timeout_minutos": STALE_LOCK_MINUTES,
        },
        "jobs": jobs,
        "etl_sync_registrado": any(j.get("id") == "etl_sync" for j in jobs),
    }