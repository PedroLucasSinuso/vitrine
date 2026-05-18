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
from app.application.scheduler_manager import dia_para_cron
from app.application.config_service import get as get_config
import logging

logger = logging.getLogger(__name__)


def _enviar_relatorio_whatsapp():
    try:
        init_db()
        with SqliteSession() as session:
            nome_loja = get_config(session, "nome_estabelecimento", "Vitrine")

            sid = get_config(session, "twilio_account_sid")
            token = get_config(session, "twilio_auth_token")
            from_num = get_config(session, "twilio_from_number")

            if not sid or not token:
                logger.warning("WhatsApp não configurado, pulando envio.")
                return

            contatos = session.execute(
                select(WhatsAppContato)
            ).scalars().all()

        numeros = [c.numero for c in contatos if c.numero.strip()]
        if not numeros:
            logger.info("WhatsApp: nenhum contato configurado, pulando.")
            return

        mensagem = construir_relatorio_semanal(nome_loja)
        client = WhatsAppClient(sid, token, from_num)
        resultados = client.enviar_para_lista(numeros, mensagem)
        logger.info("Relatório WhatsApp enviado | resultados=%s", resultados)
    except Exception as e:
        logger.error("Erro ao enviar relatório WhatsApp | erro=%s", e)


def _enviar_relatorio_email():
    try:
        init_db()
        with SqliteSession() as session:
            nome_loja = get_config(session, "nome_estabelecimento", "Vitrine")

            smtp_host = get_config(session, "smtp_host")
            smtp_port_str = get_config(session, "smtp_port", "587")
            smtp_user = get_config(session, "smtp_user")
            smtp_password = get_config(session, "smtp_password")
            email_from = get_config(session, "email_from")

            if not smtp_host:
                logger.warning("SMTP não configurado, pulando envio de email")
                return

            contatos = session.execute(
                select(EmailContato)
            ).scalars().all()

        emails = [(c.nome, c.email) for c in contatos if c.email.strip()]
        if not emails:
            logger.info("Email: nenhum contato configurado, pulando.")
            return

        assunto = f"Relatório Semanal — {nome_loja}"
        html, imagens = construir_relatorio_email(nome_loja)
        smtp_port = int(smtp_port_str)
        resultados = enviar_para_lista_com_imagens(
            emails, assunto, html, imagens,
            smtp_host=smtp_host, smtp_port=smtp_port,
            smtp_user=smtp_user, smtp_password=smtp_password,
            email_from=email_from,
        )
        logger.info("Email enviado | resultados=%s", resultados)
    except Exception as e:
        logger.error("Erro ao enviar email | erro=%s", e)


def ler_config_etl_interval() -> int:
    try:
        init_db()
        with SqliteSession() as session:
            val = get_config(session, "etl_interval_minutes", "60")
            return max(10, int(val))
    except (ValueError, TypeError):
        return 60
    except Exception:
        return 60


def ler_config_schedule_whatsapp() -> tuple[str, int, int]:
    try:
        init_db()
        with SqliteSession() as session:
            day_of_week = get_config(session, "report_day", "fri")
            time_str = get_config(session, "report_time", "18:00")
            hour, minute = map(int, time_str.split(":"))
            return day_of_week, hour, minute
    except Exception:
        return "fri", 18, 0


def ler_config_schedule_email() -> tuple[str, int, int]:
    try:
        init_db()
        with SqliteSession() as session:
            day_of_week = get_config(session, "report_email_day", "fri")
            time_str = get_config(session, "report_email_time", "18:00")
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
