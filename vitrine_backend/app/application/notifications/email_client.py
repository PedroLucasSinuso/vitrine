import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr
from app.core.config import settings

logger = logging.getLogger(__name__)


def enviar_email_html(para: str, assunto: str, html: str) -> bool:
    if not settings.smtp_host:
        logger.warning("SMTP não configurado, pulando envio de email")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.email_from
        msg["To"] = para
        msg["Subject"] = assunto
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.email_from, [para], msg.as_string())

        logger.info("Email enviado | para=%s assunto=%s", para, assunto)
        return True
    except Exception as e:
        logger.error("Erro ao enviar email | para=%s erro=%s", para, e)
        return False


def enviar_email_html_com_imagens(
    para: str, assunto: str, html: str,
    imagens: list[tuple[str, bytes, str]],
) -> bool:
    """Envia email HTML com imagens embutidas via CID.

    Args:
        para: email de destino
        assunto: assunto do email
        html: corpo HTML
        imagens: lista de (cid_name, file_bytes, mimetype)
    """
    if not settings.smtp_host:
        logger.warning("SMTP não configurado, pulando envio de email")
        return False

    try:
        msg = MIMEMultipart("related")
        msg["From"] = settings.email_from
        msg["To"] = para
        msg["Subject"] = assunto
        msg.attach(MIMEText(html, "html", "utf-8"))

        for cid, data, mime in imagens:
            img = MIMEImage(data, _subtype=mime.split("/")[-1])
            img.add_header("Content-ID", f"<{cid}>")
            img.add_header("Content-Disposition", "inline", filename=cid)
            msg.attach(img)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.email_from, [para], msg.as_string())

        logger.info("Email com imagens enviado | para=%s assunto=%s", para, assunto)
        return True
    except Exception as e:
        logger.error("Erro ao enviar email com imagens | para=%s erro=%s", para, e)
        return False


def enviar_para_lista(contatos: list[tuple[str, str]], assunto: str, html: str) -> dict[str, bool]:
    resultados: dict[str, bool] = {}
    for nome, email in contatos:
        resultados[email] = enviar_email_html(email, assunto, html)
    return resultados


def enviar_para_lista_com_imagens(
    contatos: list[tuple[str, str]], assunto: str, html: str,
    imagens: list[tuple[str, bytes, str]],
) -> dict[str, bool]:
    resultados: dict[str, bool] = {}
    for nome, email in contatos:
        resultados[email] = enviar_email_html_com_imagens(email, assunto, html, imagens)
    return resultados
