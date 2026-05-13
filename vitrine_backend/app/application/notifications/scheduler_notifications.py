from apscheduler.schedulers.background import BackgroundScheduler
from app.application.notifications.whatsapp_client import WhatsAppClient
from app.application.notifications.report_builder import construir_relatorio_semanal
from app.application.notifications.report_builder_email import construir_relatorio_email
from app.application.notifications.email_client import (
    enviar_para_lista,
    enviar_para_lista_com_imagens,
)
from app.domain.models.whatsapp_contato import WhatsAppContato
from app.domain.models.email_contato import EmailContato
from app.infrastructure.db.session import SqliteSession
from sqlalchemy import select
from app.infrastructure.db.bootstrap import init_db
from app.domain.models.configuracao import Configuracao
from app.application.scheduler_manager import dia_para_cron
import logging

logger = logging.getLogger(__name__)


def _enviar_relatorio_whatsapp():
    try:
        init_db()
        with SqliteSession() as session:
            nome_raw = session.execute(
                select(Configuracao).where(Configuracao.chave == "market_name")
            ).scalar_one_or_none()
            nome_loja = nome_raw.valor if nome_raw else "Vitrine"

            contatos = session.execute(
                select(WhatsAppContato)
            ).scalars().all()

        numeros = [c.numero for c in contatos if c.numero.strip()]
        if not numeros:
            logger.info("WhatsApp: nenhum contato configurado, pulando.")
            return

        mensagem = construir_relatorio_semanal(nome_loja)
        client = WhatsAppClient()
        resultados = client.enviar_para_lista(numeros, mensagem)
        logger.info("Relatório WhatsApp enviado | resultados=%s", resultados)
    except Exception as e:
        logger.error("Erro ao enviar relatório WhatsApp | erro=%s", e)


def _enviar_relatorio_email():
    try:
        init_db()
        with SqliteSession() as session:
            from app.domain.models.configuracao import Configuracao
            nome_raw = session.execute(
                select(Configuracao).where(Configuracao.chave == "market_name")
            ).scalar_one_or_none()
            nome_loja = nome_raw.valor if nome_raw else "Vitrine"

            contatos = session.execute(
                select(EmailContato)
            ).scalars().all()

        emails = [(c.nome, c.email) for c in contatos if c.email.strip()]
        if not emails:
            logger.info("Teste email: nenhum contato configurado, pulando.")
            return

        assunto = f"Relatório Semanal — {nome_loja}"
        html, imagens = construir_relatorio_email(nome_loja)
        resultados = enviar_para_lista_com_imagens(emails, assunto, html, imagens)
        logger.info("Teste email enviado | resultados=%s", resultados)
    except Exception as e:
        logger.error("Erro ao enviar email de teste | erro=%s", e)


def _read_config_str(key: str, default: str) -> str:
    try:
        init_db()
        with SqliteSession() as session:
            raw = session.execute(
                select(Configuracao).where(Configuracao.chave == key)
            ).scalar_one_or_none()
            return raw.valor.strip() if raw else default
    except Exception:
        return default


def ler_config_etl_interval() -> int:
    val = _read_config_str("etl_interval_minutes", "60")
    try:
        return max(10, int(val))
    except (ValueError, TypeError):
        return 60


def ler_config_schedule_whatsapp() -> tuple[str, int, int]:
    try:
        day_of_week = _read_config_str("report_day", "fri")
        time_str = _read_config_str("report_time", "18:00")
        hour, minute = map(int, time_str.split(":"))
        return day_of_week, hour, minute
    except Exception:
        return "fri", 18, 0


def ler_config_schedule_email() -> tuple[str, int, int]:
    try:
        day_of_week = _read_config_str("report_email_day", "fri")
        time_str = _read_config_str("report_email_time", "18:00")
        hour, minute = map(int, time_str.split(":"))
        return day_of_week, hour, minute
    except Exception:
        return "fri", 18, 0


def iniciar_scheduler_notificacoes(scheduler: BackgroundScheduler):
    # WhatsApp job
    dia_wpp, hora_wpp, min_wpp = ler_config_schedule_whatsapp()
    scheduler.add_job(
        _enviar_relatorio_whatsapp,
        trigger="cron",
        day_of_week=dia_para_cron(dia_wpp),
        hour=hora_wpp,
        minute=min_wpp,
        id="relatorio_whatsapp",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Job WhatsApp registrado | dia=%s horario=%02d:%02d", dia_wpp, hora_wpp, min_wpp)

    # Email job
    dia_email, hora_email, min_email = ler_config_schedule_email()
    scheduler.add_job(
        _enviar_relatorio_email,
        trigger="cron",
        day_of_week=dia_para_cron(dia_email),
        hour=hora_email,
        minute=min_email,
        id="relatorio_email",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Job Email registrado | dia=%s horario=%02d:%02d", dia_email, hora_email, min_email)
