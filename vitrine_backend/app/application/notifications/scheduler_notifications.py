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
from app.domain.models.empresa import Empresa
from app.infrastructure.db.session import SqliteSession
from sqlalchemy import select
from app.infrastructure.db.bootstrap import init_db
from app.application.scheduler_manager import dia_para_cron, reagendar_etl, reagendar_relatorio_whatsapp, reagendar_relatorio_email
from app.application.config_service import get as get_config
from app.application.config_service import montar_url_postgres
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.adapters.alterdata.transaction_source import AlterdataTransactionSource
import logging

logger = logging.getLogger(__name__)


def _obter_transaction_source(db: Session, empresa_id: int) -> AlterdataTransactionSource | None:
    """Cria um TransactionSource a partir das configs de ERP DA EMPRESA no SQLite."""
    try:
        url = montar_url_postgres(db, empresa_id)
        if not url:
            logger.warning("ERP não configurado | empresa_id=%s — pulando envio de relatório", empresa_id)
            return None
        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=3,
            connect_args={"connect_timeout": 10},
        )
        return AlterdataTransactionSource(engine)
    except Exception as e:
        logger.error("Erro ao conectar no ERP | empresa_id=%s erro=%s", empresa_id, e)
        return None


def _enviar_relatorio_whatsapp(empresa_id: int):
    try:
        init_db()
        with SqliteSession() as session:
            nome_loja = get_config(session, empresa_id, "nome_estabelecimento", "Vitrine")

            sid = get_config(session, empresa_id, "twilio_account_sid")
            token = get_config(session, empresa_id, "twilio_auth_token")
            from_num = get_config(session, empresa_id, "twilio_from_number")

            if not sid or not token:
                logger.warning("WhatsApp não configurado | empresa_id=%s — pulando envio.", empresa_id)
                return

            source = _obter_transaction_source(session, empresa_id)
            if source is None:
                return

            contatos = session.execute(
                select(WhatsAppContato).where(WhatsAppContato.empresa_id == empresa_id)
            ).scalars().all()

            numeros = [c.numero for c in contatos if c.numero.strip()]
            if not numeros:
                logger.info("WhatsApp: nenhum contato configurado | empresa_id=%s — pulando.", empresa_id)
                return

            mensagem = construir_relatorio_semanal(nome_loja, source)

        client = WhatsAppClient(sid, token, from_num)
        resultados = client.enviar_para_lista(numeros, mensagem)
        logger.info("Relatório WhatsApp enviado | empresa_id=%s resultados=%s", empresa_id, resultados)
    except Exception as e:
        logger.error("Erro ao enviar relatório WhatsApp | empresa_id=%s erro=%s", empresa_id, e)


def _enviar_relatorio_email(empresa_id: int):
    try:
        init_db()
        with SqliteSession() as session:
            nome_loja = get_config(session, empresa_id, "nome_estabelecimento", "Vitrine")

            smtp_host = get_config(session, empresa_id, "smtp_host")
            smtp_port_str = get_config(session, empresa_id, "smtp_port", "587")
            smtp_user = get_config(session, empresa_id, "smtp_user")
            smtp_password = get_config(session, empresa_id, "smtp_password")
            email_from = get_config(session, empresa_id, "email_from")

            if not smtp_host:
                logger.warning("SMTP não configurado | empresa_id=%s — pulando envio de email", empresa_id)
                return

            source = _obter_transaction_source(session, empresa_id)
            if source is None:
                return

            contatos = session.execute(
                select(EmailContato).where(EmailContato.empresa_id == empresa_id)
            ).scalars().all()

            emails = [(c.nome, c.email) for c in contatos if c.email.strip()]
            if not emails:
                logger.info("Email: nenhum contato configurado | empresa_id=%s — pulando.", empresa_id)
                return

            assunto = f"Relatório Semanal — {nome_loja}"
            html, imagens, anexo_bytes = construir_relatorio_email(nome_loja, source)
            smtp_port = int(smtp_port_str)

        # Monta anexo se houver
        anexos = None
        if anexo_bytes:
            anexos = [(anexo_bytes, "relatorio_semanal.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")]

        # Envio fora do with (não precisa de sessão)
        resultados = enviar_para_lista_com_imagens(
            emails, assunto, html, imagens,
            smtp_host=smtp_host, smtp_port=smtp_port,
            smtp_user=smtp_user, smtp_password=smtp_password,
            email_from=email_from,
            anexos=anexos,
        )
        logger.info("Email enviado | empresa_id=%s resultados=%s", empresa_id, resultados)
    except Exception as e:
        logger.error("Erro ao enviar email | empresa_id=%s erro=%s", empresa_id, e)


def ler_config_etl_interval(empresa_id: int) -> int:
    try:
        init_db()
        with SqliteSession() as session:
            val = get_config(session, empresa_id, "etl_interval_minutes", "60")
            return max(10, int(val))
    except (ValueError, TypeError):
        return 60
    except Exception:
        return 60


def ler_config_schedule_whatsapp(empresa_id: int) -> tuple[str, int, int]:
    try:
        init_db()
        with SqliteSession() as session:
            day_of_week = get_config(session, empresa_id, "report_day", "fri")
            time_str = get_config(session, empresa_id, "report_time", "18:00")
            hour, minute = map(int, time_str.split(":"))
            return day_of_week, hour, minute
    except Exception:
        return "fri", 18, 0


def ler_config_schedule_email(empresa_id: int) -> tuple[str, int, int]:
    try:
        init_db()
        with SqliteSession() as session:
            day_of_week = get_config(session, empresa_id, "report_email_day", "fri")
            time_str = get_config(session, empresa_id, "report_email_time", "18:00")
            hour, minute = map(int, time_str.split(":"))
            return day_of_week, hour, minute
    except Exception:
        return "fri", 18, 0


def iniciar_scheduler_notificacoes(scheduler: BackgroundScheduler):
    """Registra os jobs de relatório (WhatsApp/Email) de CADA empresa ativa,
    cada um com o próprio dia/horário configurado (ver scheduler_manager.py).
    """
    with SqliteSession() as session:
        empresas = session.execute(
            select(Empresa).where(Empresa.status == "ativa")
        ).scalars().all()
        empresa_ids = [e.id for e in empresas]

    for empresa_id in empresa_ids:
        dia_wpp, hora_wpp, min_wpp = ler_config_schedule_whatsapp(empresa_id)
        reagendar_relatorio_whatsapp(
            empresa_id, dia_wpp, hora_wpp, min_wpp,
            lambda eid=empresa_id: _enviar_relatorio_whatsapp(eid),
        )
        logger.info(
            "Job WhatsApp registrado | empresa_id=%s dia=%s horario=%02d:%02d",
            empresa_id, dia_wpp, hora_wpp, min_wpp,
        )

        dia_email, hora_email, min_email = ler_config_schedule_email(empresa_id)
        reagendar_relatorio_email(
            empresa_id, dia_email, hora_email, min_email,
            lambda eid=empresa_id: _enviar_relatorio_email(eid),
        )
        logger.info(
            "Job Email registrado | empresa_id=%s dia=%s horario=%02d:%02d",
            empresa_id, dia_email, hora_email, min_email,
        )
