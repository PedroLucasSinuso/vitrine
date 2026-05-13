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
import logging

logger = logging.getLogger(__name__)


def _enviar_relatorio():
    try:
        init_db()
        with SqliteSession() as session:
            from app.domain.models.configuracao import Configuracao
            nome_raw = session.execute(
                select(Configuracao).where(Configuracao.chave == "market_name")
            ).scalar_one_or_none()
            nome_loja = nome_raw.valor if nome_raw else "Vitrine"

            contatos_wpp = session.execute(
                select(WhatsAppContato)
            ).scalars().all()

            contatos_email = session.execute(
                select(EmailContato)
            ).scalars().all()

        numeros = [c.numero for c in contatos_wpp if c.numero.strip()]
        if numeros:
            mensagem = construir_relatorio_semanal(nome_loja)
            client = WhatsAppClient()
            resultados_wpp = client.enviar_para_lista(numeros, mensagem)
            logger.info("Relatório WhatsApp enviado | resultados=%s", resultados_wpp)
        else:
            logger.info("Relatório WhatsApp: nenhum contato configurado, pulando.")

        emails = [(c.nome, c.email) for c in contatos_email if c.email.strip()]
        if emails:
            assunto = f"Relatório Semanal — {nome_loja}"
            html, imagens = construir_relatorio_email(nome_loja)
            resultados_email = enviar_para_lista_com_imagens(emails, assunto, html, imagens)
            logger.info("Relatório email enviado | resultados=%s", resultados_email)
        else:
            logger.info("Relatório email: nenhum contato configurado, pulando.")
    except Exception as e:
        logger.error("Erro ao enviar relatório semanal | erro=%s", e)


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


def _enviar_relatorio_whatsapp():
    try:
        init_db()
        with SqliteSession() as session:
            from app.domain.models.configuracao import Configuracao
            nome_raw = session.execute(
                select(Configuracao).where(Configuracao.chave == "market_name")
            ).scalar_one_or_none()
            nome_loja = nome_raw.valor if nome_raw else "Vitrine"

            contatos = session.execute(
                select(WhatsAppContato)
            ).scalars().all()

        numeros = [c.numero for c in contatos if c.numero.strip()]
        if not numeros:
            logger.info("Relatório WhatsApp: nenhum contato configurado, pulando.")
            return

        mensagem = construir_relatorio_semanal(nome_loja)
        client = WhatsAppClient()
        resultados = client.enviar_para_lista(numeros, mensagem)
        logger.info("Relatório semanal enviado | resultados=%s", resultados)
    except Exception as e:
        logger.error("Erro ao enviar relatório semanal | erro=%s", e)


def _ler_config_schedule() -> tuple[str, int, int]:
    try:
        init_db()
        with SqliteSession() as session:
            day_raw = session.execute(
                select(Configuracao).where(Configuracao.chave == "report_day")
            ).scalar_one_or_none()
            time_raw = session.execute(
                select(Configuracao).where(Configuracao.chave == "report_time")
            ).scalar_one_or_none()

        day_of_week = day_raw.valor.strip().lower() if day_raw else "fri"
        report_time = time_raw.valor.strip() if time_raw else "18:00"

        try:
            hour, minute = map(int, report_time.split(":"))
        except (ValueError, AttributeError):
            hour, minute = 18, 0

        return day_of_week, hour, minute
    except Exception:
        logger.warning("Não foi possível ler schedule do banco, usando padrão (sexta 18:00)")
        return "fri", 18, 0


def _dia_semana_para_cron(dia: str) -> str:
    mapa = {
        "sunday": "sun", "monday": "mon", "tuesday": "tue", "wednesday": "wed",
        "thursday": "thu", "friday": "fri", "saturday": "sat",
        "domingo": "sun", "segunda": "mon", "terca": "tue", "quarta": "wed",
        "quinta": "thu", "sexta": "fri", "sabado": "sat",
    }
    return mapa.get(dia.lower()[:3], "fri")


def iniciar_scheduler_notificacoes(scheduler: BackgroundScheduler):
    dia, hora, minuto = _ler_config_schedule()
    cron_dia = _dia_semana_para_cron(dia)

    scheduler.add_job(
        _enviar_relatorio,
        trigger="cron",
        day_of_week=cron_dia,
        hour=hora,
        minute=minuto,
        id="relatorio_semanal",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Job de relatório semanal registrado | dia=%s horario=%02d:%02d", cron_dia, hora, minuto)
