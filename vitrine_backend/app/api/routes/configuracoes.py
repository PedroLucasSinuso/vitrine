import os
import shutil
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy import select, create_engine, text
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.schemas.configuracao_schema import (
    LogoUploadResponse,
    ConfiguracaoResponse,
    ConfiguracaoUpdate,
)
from app.domain.models.configuracao import Configuracao
from app.domain.models.usuario import Usuario
from app.infrastructure.db.bootstrap import init_db
from app.application.scheduler_manager import (
    reagendar_etl,
    reagendar_relatorio_whatsapp,
    reagendar_relatorio_email,
)
from app.application.notifications.scheduler_notifications import (
    _enviar_relatorio_whatsapp,
    _enviar_relatorio_email,
)
from app.application.config_service import (
    set_many,
    invalidar_cache,
    get as get_config,
    is_sensitive,
    CHAVES_EDITAVEIS,
)
from app.core.error_handler import sanitizar_erro

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")


@router.get("/configuracoes", response_model=ConfiguracaoResponse)
def listar_configuracoes(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    init_db()
    stmt = select(Configuracao)
    results = db.execute(stmt).scalars().all()
    return ConfiguracaoResponse(
        configuracoes={
            r.chave: (
                "***configurado***"
                if is_sensitive(r.chave) and r.valor
                else r.valor
            )
            for r in results
        }
    )


@router.patch("/configuracoes", response_model=ConfiguracaoResponse)
def atualizar_configuracoes(
    body: ConfiguracaoUpdate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    init_db()
    set_many(db, body.valores)

    valores = body.valores

    if "etl_interval_minutes" in valores:
        try:
            reagendar_etl(max(10, int(valores["etl_interval_minutes"])))
        except Exception as e:
            logger.error("Erro ao reagendar ETL: %s", e)

    if "report_day" in valores or "report_time" in valores:
        try:
            dia = get_config(db, "report_day", "fri")
            time_str = get_config(db, "report_time", "18:00")
            hora, minuto = map(int, time_str.split(":"))
            reagendar_relatorio_whatsapp(dia, hora, minuto, _enviar_relatorio_whatsapp)
        except Exception as e:
            logger.error("Erro ao reagendar WhatsApp: %s", e)

    if "report_email_day" in valores or "report_email_time" in valores:
        try:
            dia = get_config(db, "report_email_day", "fri")
            time_str = get_config(db, "report_email_time", "18:00")
            hora, minuto = map(int, time_str.split(":"))
            reagendar_relatorio_email(dia, hora, minuto, _enviar_relatorio_email)
        except Exception as e:
            logger.error("Erro ao reagendar Email: %s", e)

    stmt = select(Configuracao)
    results = db.execute(stmt).scalars().all()
    return ConfiguracaoResponse(
        configuracoes={
            r.chave: (
                "***configurado***"
                if is_sensitive(r.chave) and r.valor
                else r.valor
            )
            for r in results
        }
    )


@router.post("/configuracoes/testar-erp")
def testar_conexao_erp(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    """Testa a conexão com o banco do ERP com as credenciais atuais."""
    url = get_config(db, "erp_postgres_url")
    if not url:
        raise HTTPException(status_code=400, detail="URL do ERP não configurada")
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "mensagem": "Conexão estabelecida com sucesso"}
    except Exception as e:
        return {"status": "erro", "mensagem": sanitizar_erro(e)}


@router.post("/configuracoes/testar-whatsapp")
def testar_whatsapp(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    """Envia um relatório de teste via WhatsApp para os contatos configurados."""
    sid = get_config(db, "twilio_account_sid")
    token = get_config(db, "twilio_auth_token")
    if not sid or not token:
        raise HTTPException(status_code=400, detail="WhatsApp não configurado")
    _enviar_relatorio_whatsapp()
    return {"status": "ok", "mensagem": "Relatório de teste enviado via WhatsApp"}


@router.post("/configuracoes/testar-email")
def testar_email(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    """Envia um relatório de teste por e-mail para os contatos configurados."""
    smtp_host = get_config(db, "smtp_host")
    if not smtp_host:
        raise HTTPException(status_code=400, detail="SMTP não configurado")
    _enviar_relatorio_email()
    return {"status": "ok", "mensagem": "Relatório de teste enviado por e-mail"}


@router.post("/configuracoes/logo", response_model=LogoUploadResponse, status_code=201)
def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    os.makedirs(STATIC_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename or "logo.png")[1] or ".png"
    filename = f"logo{ext}"
    filepath = os.path.join(STATIC_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    logo_url = f"/static/{filename}"

    set_many(db, {"logo_url": logo_url})

    return {"logo_url": logo_url}
