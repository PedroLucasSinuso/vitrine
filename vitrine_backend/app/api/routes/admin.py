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


def _run_sync_background(job_id: str, empresa_id: int):
    from app.infrastructure.db.bootstrap import init_db
    from app.infrastructure.db.session import SqliteSession
    from app.application.erp_factory import run_sync_common

    init_db()
    session = SqliteSession()

    try:
        job = session.query(SyncJob).filter(
            SyncJob.job_id == job_id, SyncJob.empresa_id == empresa_id
        ).first()
        if not job:
            logger.error("SyncJob %s not found in DB | empresa_id=%s", job_id, empresa_id)
            return
        job.started_at = datetime.now(timezone.utc)
        job.status = "em_progresso"
        session.commit()
        logger.info("Sync job %s iniciado em background | empresa_id=%s", job_id, empresa_id)

        # run_sync_common cuida de engine, source, service.sync(),
        # invalidação de cache e engine.dispose()
        result = run_sync_common(session, empresa_id=empresa_id, job_id=job_id, pool_size=1)

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

    except Exception as e:
        session.rollback()
        logar_erro_interno(f"Sync job {job_id} falhou", e)
        try:
            job = session.query(SyncJob).filter(
                SyncJob.job_id == job_id, SyncJob.empresa_id == empresa_id
            ).first()
            if job:
                job.status = "erro"
                job.finished_at = datetime.now(timezone.utc)
                job.error_message = sanitizar_erro(e)
                session.commit()
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
        empresa_id=_admin.empresa_id,
        job_id=job_id,
        status="em_progresso",
        started_at=now,
    )
    db.add(job)
    db.commit()

    executor.submit(_run_sync_background, job_id, _admin.empresa_id)

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
    job = db.query(SyncJob).filter(
        SyncJob.job_id == job_id, SyncJob.empresa_id == _admin.empresa_id
    ).first()

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
        .where(SyncJob.empresa_id == _admin.empresa_id)
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
    total_count = db.query(SyncJob).filter(SyncJob.empresa_id == _admin.empresa_id).count()
    return SyncListResponse(jobs=jobs, total=total_count)


@router.get("/scheduler/jobs")
def get_scheduler_jobs(
    _admin: Usuario = Depends(require_admin),
):
    return {"jobs": listar_jobs()}