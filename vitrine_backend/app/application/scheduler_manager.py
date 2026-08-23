from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import logging

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def init_scheduler_manager(scheduler: BackgroundScheduler):
    global _scheduler
    _scheduler = scheduler


def get_scheduler() -> BackgroundScheduler:
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized")
    return _scheduler


_DIA_MAPA = {
    "sun": "sun", "mon": "mon", "tue": "tue", "wed": "wed",
    "thu": "thu", "fri": "fri", "sat": "sat",
    "dom": "sun", "seg": "mon", "ter": "tue", "qua": "wed",
    "qui": "thu", "sex": "fri", "sab": "sat",
}


def dia_para_cron(dia: str) -> str:
    return _DIA_MAPA.get(dia.lower()[:3], "fri")


def _reschedule_or_add(job_id: str, trigger: str, func, **trigger_args):
    sched = get_scheduler()
    existing = sched.get_job(job_id)
    if existing:
        sched.reschedule_job(job_id, trigger=trigger, **trigger_args)
    elif func is not None:
        sched.add_job(
            func, trigger=trigger,
            id=job_id, replace_existing=True,
            misfire_grace_time=3600,
            **trigger_args
        )
    else:
        logger.warning("Job %s nao encontrado e sem func para recriar", job_id)
        return

    job = sched.get_job(job_id)
    if job:
        logger.info("Job %s | proxima_execucao=%s", job_id, job.next_run_time)


# ── Jobs por empresa (multi-tenant) ──────────────────────────────────
#
# Cada empresa tem seu próprio job de ETL e de relatórios, com seu próprio
# horário/intervalo configurado (Configuracao é por tenant desde a Fase 1
# do plano de SaaS). Job IDs seguem o padrão "{tipo}_{empresa_id}" — sem
# isso, a última empresa a salvar sua configuração sobrescreveria o
# horário de todas as outras (um único job global compartilhado).

def reagendar_etl(empresa_id: int, intervalo_minutos: int, func=None):
    _reschedule_or_add(f"etl_sync_{empresa_id}", "interval", func, minutes=intervalo_minutos)
    logger.info("ETL job atualizado | empresa_id=%s intervalo=%d min", empresa_id, intervalo_minutos)


def reagendar_relatorio_whatsapp(empresa_id: int, dia: str, hora: int, minuto: int, func=None):
    _reschedule_or_add(
        f"relatorio_whatsapp_{empresa_id}", "cron", func,
        day_of_week=dia_para_cron(dia), hour=hora, minute=minuto,
    )


def reagendar_relatorio_email(empresa_id: int, dia: str, hora: int, minuto: int, func=None):
    _reschedule_or_add(
        f"relatorio_email_{empresa_id}", "cron", func,
        day_of_week=dia_para_cron(dia), hour=hora, minute=minuto,
    )


def remover_jobs_da_empresa(empresa_id: int) -> None:
    """Remove os 3 jobs de uma empresa (usado ao suspender/excluir um tenant)."""
    sched = get_scheduler()
    for job_id in (f"etl_sync_{empresa_id}", f"relatorio_whatsapp_{empresa_id}", f"relatorio_email_{empresa_id}"):
        try:
            sched.remove_job(job_id)
        except JobLookupError:
            pass


def listar_jobs() -> list[dict]:
    sched = get_scheduler()
    jobs = []
    for job in sched.get_jobs():
        jobs.append({
            "id": job.id,
            "trigger": str(job.trigger),
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })
    return jobs
