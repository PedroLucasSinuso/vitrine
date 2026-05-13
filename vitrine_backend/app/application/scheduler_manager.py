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


def reagendar_etl(intervalo_minutos: int, func=None):
    _reschedule_or_add("etl_sync", "interval", func, minutes=intervalo_minutos)
    logger.info("ETL job atualizado | intervalo=%d min", intervalo_minutos)


def reagendar_relatorio_whatsapp(dia: str, hora: int, minuto: int, func=None):
    _reschedule_or_add(
        "relatorio_whatsapp", "cron", func,
        day_of_week=dia_para_cron(dia), hour=hora, minute=minuto,
    )


def reagendar_relatorio_email(dia: str, hora: int, minuto: int, func=None):
    _reschedule_or_add(
        "relatorio_email", "cron", func,
        day_of_week=dia_para_cron(dia), hour=hora, minute=minuto,
    )


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
