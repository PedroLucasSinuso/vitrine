from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
import logging

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone=ZoneInfo("America/Sao_Paulo"))


def iniciar_scheduler() -> BackgroundScheduler:
    _scheduler.start()
    logger.info("Scheduler iniciado")
    return _scheduler


def parar_scheduler():
    _scheduler.shutdown()
