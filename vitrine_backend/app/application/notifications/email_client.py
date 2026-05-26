import smtplib
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.utils import formataddr

_MAX_WORKERS = 4

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
    anexos: list[tuple[bytes, str, str]] | None = None,
) -> bool:
    """Envia email HTML (com ou sem imagens embutidas) com anexos opcionais."""
    if not smtp_host:
        logger.warning("SMTP não configurado, pulando envio de email")
        return False

    try:
        # ── Corpo principal (HTML + imagens) ──
        corpo = MIMEMultipart("alternative")
        corpo.attach(MIMEText(html, "html", "utf-8"))

        if imagens:
            related = MIMEMultipart("related")
            related.attach(corpo)
            for cid, data, mime in imagens:
                img = MIMEImage(data, _subtype=mime.split("/")[-1])
                img.add_header("Content-ID", f"<{cid}>")
                img.add_header("Content-Disposition", "inline", filename=cid)
                related.attach(img)
            corpo = related

        # ── Estrutura final com anexos ──
        if anexos:
            msg = MIMEMultipart("mixed")
            msg.attach(corpo)
            for conteudo, nome_arquivo, mime_type in anexos:
                part = MIMEBase(*mime_type.split("/", 1))
                part.set_payload(conteudo)
                import email.encoders
                email.encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=nome_arquivo,
                )
                msg.attach(part)
        else:
            msg = corpo

        msg["From"] = email_from
        msg["To"] = para
        msg["Subject"] = assunto

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(email_from, [para], msg.as_string())

        logger.info("Email enviado | para=%s assunto=%s anexos=%s", para, assunto, len(anexos) if anexos else 0)
        return True
    except Exception as e:
        logger.error("Erro ao enviar email | para=%s erro=%s", para, e)
        return False


def enviar_email_html(
    para: str, assunto: str, html: str,
    smtp_host: str = "", smtp_port: int = 587,
    smtp_user: str = "", smtp_password: str = "",
    email_from: str = "",
    anexos: list[tuple[bytes, str, str]] | None = None,
) -> bool:
    return _enviar(para, assunto, html, None, smtp_host, smtp_port, smtp_user, smtp_password, email_from, anexos=anexos)


def enviar_email_html_com_imagens(
    para: str, assunto: str, html: str,
    imagens: list[tuple[str, bytes, str]],
    smtp_host: str = "", smtp_port: int = 587,
    smtp_user: str = "", smtp_password: str = "",
    email_from: str = "",
    anexos: list[tuple[bytes, str, str]] | None = None,
) -> bool:
    return _enviar(para, assunto, html, imagens, smtp_host, smtp_port, smtp_user, smtp_password, email_from, anexos=anexos)


def _enviar_paralelo(
    contatos: list[tuple[str, str]],
    assunto: str,
    html: str,
    imagens: list[tuple[str, bytes, str]] | None,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    email_from: str,
    anexos: list[tuple[bytes, str, str]] | None,
    com_imagens: bool,
) -> dict[str, bool]:
    """Envia email para múltiplos contatos em paralelo (ThreadPoolExecutor)."""
    resultados: dict[str, bool] = {}
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        futuros = {}
        for nome, email in contatos:
            if com_imagens:
                fut = executor.submit(
                    enviar_email_html_com_imagens, email, assunto, html, imagens or [],
                    smtp_host, smtp_port, smtp_user, smtp_password, email_from, anexos,
                )
            else:
                fut = executor.submit(
                    enviar_email_html, email, assunto, html,
                    smtp_host, smtp_port, smtp_user, smtp_password, email_from, anexos,
                )
            futuros[fut] = email

        for fut in as_completed(futuros):
            email = futuros[fut]
            try:
                resultados[email] = fut.result()
            except Exception as e:
                logger.error("Erro inesperado no envio paralelo | email=%s erro=%s", email, e)
                resultados[email] = False
    return resultados


def enviar_para_lista(
    contatos: list[tuple[str, str]], assunto: str, html: str,
    smtp_host: str = "", smtp_port: int = 587,
    smtp_user: str = "", smtp_password: str = "",
    email_from: str = "",
    anexos: list[tuple[bytes, str, str]] | None = None,
) -> dict[str, bool]:
    return _enviar_paralelo(
        contatos, assunto, html, None,
        smtp_host, smtp_port, smtp_user, smtp_password, email_from, anexos,
        com_imagens=False,
    )


def enviar_para_lista_com_imagens(
    contatos: list[tuple[str, str]], assunto: str, html: str,
    imagens: list[tuple[str, bytes, str]],
    smtp_host: str = "", smtp_port: int = 587,
    smtp_user: str = "", smtp_password: str = "",
    email_from: str = "",
    anexos: list[tuple[bytes, str, str]] | None = None,
) -> dict[str, bool]:
    return _enviar_paralelo(
        contatos, assunto, html, imagens,
        smtp_host, smtp_port, smtp_user, smtp_password, email_from, anexos,
        com_imagens=True,
    )
