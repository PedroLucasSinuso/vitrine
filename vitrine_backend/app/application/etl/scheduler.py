from apscheduler.schedulers.background import BackgroundScheduler
from app.application.etl.pipeline import run_etl
import logging

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler()


def iniciar_scheduler(intervalo_horas: int = 1) -> BackgroundScheduler:
    _scheduler.add_job(
        run_etl,
        "interval",
        hours=intervalo_horas,
        id="etl_sync",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler ETL iniciado | intervalo=%sh", intervalo_horas)
    return _scheduler


def parar_scheduler():
    _scheduler.shutdown()
