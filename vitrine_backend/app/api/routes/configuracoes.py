import os
import shutil
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy import select, create_engine, text
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.api.deps import get_db, require_admin
from app.schemas.configuracao_schema import (
    LogoUploadResponse,
    ConfiguracaoResponse,
    ConfiguracaoUpdate,
)
from app.schemas.endereco_schema import extrair_endereco_update
from app.domain.models.configuracao import Configuracao
from app.domain.models.cache_status import CacheStatus
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
    get_decrypted,
    montar_url_postgres,
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

    # Valida campos de endereço antes de salvar
    try:
        extrair_endereco_update(body.valores)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

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
    url = montar_url_postgres(db)
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


# ── Cache Status ─────────────────────────────────────────────────────


@router.get("/cache/status")
def get_cache_status(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    """Retorna o status do cache de produtos (última sincronia ETL)."""
    stmt = select(CacheStatus).order_by(CacheStatus.id.desc())
    result = db.execute(stmt).scalars().first()
    return {
        "produtos_cached": result is not None,
        "last_refresh": result.last_updated if result else None,
        "ttl_seconds": 30,
    }


# ── Teste Anthropic ──────────────────────────────────────────────────


@router.post("/configuracoes/testar-anthropic")
def testar_anthropic(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    """Testa a conexão com a API da Anthropic usando a chave configurada."""
    api_key = get_decrypted(db, "anthropic_api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="Anthropic API Key não configurada")

    try:
        import httpx
        with httpx.Client(timeout=10) as client:
            resp = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Say OK"}],
                },
            )
            if resp.status_code == 200:
                return {"status": "ok", "mensagem": "Conexão com Anthropic estabelecida"}
            else:
                return {
                    "status": "erro",
                    "mensagem": f"HTTP {resp.status_code}: {resp.text[:200]}",
                }
    except Exception as e:
        return {"status": "erro", "mensagem": sanitizar_erro(e)}
