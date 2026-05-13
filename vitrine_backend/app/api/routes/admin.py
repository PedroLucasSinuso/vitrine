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
from app.domain.models.cache_status import CacheStatus
from app.domain.models.usuario import Usuario
from app.application.etl.pipeline import run_etl, EtlResult
from app.core.error_handler import sanitizar_erro, logar_erro_interno
from app.application.scheduler_manager import listar_jobs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

executor = ThreadPoolExecutor(max_workers=1)

JOB_STORE: dict[str, dict] = {}


def _run_etl_background(job_id: str):
    from app.infrastructure.db.bootstrap import init_db
    init_db()

    JOB_STORE[job_id]["started_at"] = datetime.now(timezone.utc)
    JOB_STORE[job_id]["status"] = "em_progresso"
    logger.info("Sync job %s iniciado em background", job_id)

    try:
        result: EtlResult = run_etl()

        JOB_STORE[job_id]["status"] = "sucesso"
        JOB_STORE[job_id]["finished_at"] = datetime.now(timezone.utc)
        JOB_STORE[job_id]["produtos_count"] = result.produtos_count
        JOB_STORE[job_id]["codigos_count"] = result.codigos_count

        logger.info(
            "Sync job %s concluído | produtos=%s codigos=%s",
            job_id, result.produtos_count, result.codigos_count
        )

    except Exception as e:
        logar_erro_interno(f"Sync job {job_id} falhou", e)
        JOB_STORE[job_id]["status"] = "erro"
        JOB_STORE[job_id]["finished_at"] = datetime.now(timezone.utc)
        JOB_STORE[job_id]["error_message"] = sanitizar_erro(e)


@router.post("/sync", response_model=SyncTriggerResponse, status_code=201)
def trigger_sync(
    _admin: Usuario = Depends(require_admin)
):
    job_id = str(uuid.uuid4())[:8]

    JOB_STORE[job_id] = {
        "job_id": job_id,
        "started_at": datetime.now(timezone.utc),
        "finished_at": None,
        "status": "em_progresso",
        "produtos_count": None,
        "codigos_count": None,
        "error_message": None,
    }

    executor.submit(_run_etl_background, job_id)

    logger.info("Sync triggered | job_id=%s by admin=%s", job_id, _admin.username)

    return SyncTriggerResponse(
        job_id=job_id,
        status="started",
        message="Sync iniciado em background"
    )


@router.get("/sync/{job_id}", response_model=SyncStatusResponse)
def get_sync_status(
    job_id: str,
    _admin: Usuario = Depends(require_admin)
):
    sync_data = JOB_STORE.get(job_id)

    if not sync_data:
        raise HTTPException(status_code=404, detail=f"Job {job_id} não encontrado")

    return SyncStatusResponse(
        job_id=sync_data["job_id"],
        started_at=sync_data["started_at"],
        finished_at=sync_data.get("finished_at"),
        status=sync_data["status"],
        produtos_count=sync_data.get("produtos_count"),
        codigos_count=sync_data.get("codigos_count"),
        error_message=sync_data.get("error_message"),
    )


@router.get("/sync", response_model=SyncListResponse)
def list_sync_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
):
    stmt = (
        select(CacheStatus)
        .order_by(CacheStatus.id.desc())
        .limit(limit)
    )
    results = db.execute(stmt).scalars().all()

    jobs = []
    for r in results:
        jobs.append(SyncStatusResponse(
            job_id=str(r.id),
            started_at=r.last_updated,
            finished_at=None,
            status=r.status,
            produtos_count=None,
            codigos_count=None,
            error_message=r.erro,
        ))

    return SyncListResponse(jobs=jobs, total=len(jobs))


@router.get("/scheduler/jobs")
def get_scheduler_jobs(
    _admin: Usuario = Depends(require_admin),
):
    return {"jobs": listar_jobs()}