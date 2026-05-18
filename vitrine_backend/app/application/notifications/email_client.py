import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr

logger = logging.getLogger(__name__)


def _enviar(
    para: str,
    assunto: str,
    html: str,
    imagens: list[tuple[str, bytes, str]] | None,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    email_from: str,
) -> bool:
    """Envia email HTML (com ou sem imagens embutidas)."""
    if not smtp_host:
        logger.warning("SMTP não configurado, pulando envio de email")
        return False

    try:
        if imagens:
            msg = MIMEMultipart("related")
            for cid, data, mime in imagens:
                img = MIMEImage(data, _subtype=mime.split("/")[-1])
                img.add_header("Content-ID", f"<{cid}>")
                img.add_header("Content-Disposition", "inline", filename=cid)
                msg.attach(img)
        else:
            msg = MIMEMultipart("alternative")

        msg["From"] = email_from
        msg["To"] = para
        msg["Subject"] = assunto
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(email_from, [para], msg.as_string())

        logger.info("Email enviado | para=%s assunto=%s", para, assunto)
        return True
    except Exception as e:
        logger.error("Erro ao enviar email | para=%s erro=%s", para, e)
        return False


def enviar_email_html(
    para: str, assunto: str, html: str,
    smtp_host: str = "", smtp_port: int = 587,
    smtp_user: str = "", smtp_password: str = "",
    email_from: str = "",
) -> bool:
    return _enviar(para, assunto, html, None, smtp_host, smtp_port, smtp_user, smtp_password, email_from)


def enviar_email_html_com_imagens(
    para: str, assunto: str, html: str,
    imagens: list[tuple[str, bytes, str]],
    smtp_host: str = "", smtp_port: int = 587,
    smtp_user: str = "", smtp_password: str = "",
    email_from: str = "",
) -> bool:
    return _enviar(para, assunto, html, imagens, smtp_host, smtp_port, smtp_user, smtp_password, email_from)


def enviar_para_lista(
    contatos: list[tuple[str, str]], assunto: str, html: str,
    smtp_host: str = "", smtp_port: int = 587,
    smtp_user: str = "", smtp_password: str = "",
    email_from: str = "",
) -> dict[str, bool]:
    resultados: dict[str, bool] = {}
    for nome, email in contatos:
        resultados[email] = enviar_email_html(
            email, assunto, html,
            smtp_host=smtp_host, smtp_port=smtp_port,
            smtp_user=smtp_user, smtp_password=smtp_password,
            email_from=email_from,
        )
    return resultados


def enviar_para_lista_com_imagens(
    contatos: list[tuple[str, str]], assunto: str, html: str,
    imagens: list[tuple[str, bytes, str]],
    smtp_host: str = "", smtp_port: int = 587,
    smtp_user: str = "", smtp_password: str = "",
    email_from: str = "",
) -> dict[str, bool]:
    resultados: dict[str, bool] = {}
    for nome, email in contatos:
        resultados[email] = enviar_email_html_com_imagens(
            email, assunto, html, imagens,
            smtp_host=smtp_host, smtp_port=smtp_port,
            smtp_user=smtp_user, smtp_password=smtp_password,
            email_from=email_from,
        )
    return resultados
