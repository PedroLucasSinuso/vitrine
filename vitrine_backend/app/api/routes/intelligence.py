"""Vitrine Intelligence — endpoints de análise semanal com IA."""
import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.limiter import limiter
from app.api.deps import get_db, require_supervisor
from app.domain.models.usuario import Usuario
from app.application.intelligence.service import solicitar_analise, consultar_job
from app.application.intelligence.dismiss import dismiss_insight as dismiss_service
from app.schemas.intelligence_schema import IntelligenceJobStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bi", tags=["Intelligence"])


@router.get("/intelligence")
@limiter.limit("3/hour")
def get_intelligence(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna análise se cache hit, ou cria job e retorna job_id.

    NOTA: TransactionSource (PostgreSQL) NÃO é dependência deste endpoint.
    A conexão PostgreSQL é criada dentro de _executar_analise (background task)
    para evitar que falhas no PostgreSQL impeçam a criação do job.
    """
    try:
        resultado, is_cached, job_id = solicitar_analise(db)
    except Exception as e:
        logger.exception("solicitar_analise falhou")
        raise HTTPException(status_code=500, detail=f"Erro ao solicitar análise: {e}")

    if is_cached and resultado:
        return resultado

    if job_id:
        from app.application.intelligence.service import _executar_analise
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, _executar_analise, job_id, data_inicio, data_fim)
        except Exception as e:
            logger.exception("Falha ao disparar background task")
            raise HTTPException(status_code=500, detail=f"Falha ao iniciar análise em background: {e}")
        return {"status": "processing", "job_id": job_id}

    # Bucket cheio — fallback já foi executado e retornou resultado
    if resultado:
        return resultado

    raise HTTPException(status_code=500, detail="Erro ao iniciar análise")


@router.get("/intelligence/status/{job_id}", response_model=IntelligenceJobStatus)
@limiter.limit("30/minute")
def get_intelligence_status(
    request: Request,
    job_id: str,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Polling de status do job."""
    status = consultar_job(db, job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return status


@router.post("/intelligence/{hash}/dismiss")
@limiter.limit("10/minute")
def dismiss_intelligence_insight(
    request: Request,
    hash: str,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Marca um insight como ignorado."""
    dismiss_service(db, hash)
    return {"status": "ok"}


@router.get("/intelligence/debug")
def debug_intelligence(
    request: Request,
    db: Session = Depends(get_db),
):
    """Endpoint de debug — sem auth. Verifica tabelas + conexão PostgreSQL.

    Uso: GET /api/bi/intelligence/debug
    """
    results = {}

    # 1. Tabelas SQLite
    from sqlalchemy import inspect, text
    inspector = inspect(db.bind)
    results["sqlite_tables"] = inspector.get_table_names()
    intelligence_tables = [t for t in results["sqlite_tables"] if 'intelligence' in t]
    results["intelligence_tables"] = intelligence_tables

    # 2. Tenta ler configuração do ERP
    try:
        from app.application.config_service import get as get_config
        erp_adapter = get_config(db, "erp_adapter", "alterdata")
        results["erp_adapter"] = erp_adapter
    except Exception as e:
        results["erp_adapter_error"] = str(e)

    # 3. Tenta conectar PostgreSQL (TransactionSource)
    try:
        from app.application.erp_factory import create_transaction_source
        source = create_transaction_source(db)
        # Tenta buscar dados
        from datetime import date, timedelta
        hoje = date.today()
        items = source.get_items(hoje - timedelta(days=7), hoje)
        results["postgres"] = {
            "connected": True,
            "items_7d": len(items),
            "sample_codes": list(set(i.product_code for i in items[:5])) if items else [],
        }
    except Exception as e:
        results["postgres"] = {"connected": False, "error": str(e)}

    return results
