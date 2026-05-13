import os
import shutil
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import select
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
        configuracoes={r.chave: r.valor for r in results}
    )


@router.patch("/configuracoes", response_model=ConfiguracaoResponse)
def atualizar_configuracoes(
    body: ConfiguracaoUpdate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
):
    init_db()
    now = datetime.now(timezone.utc)
    for chave, valor in body.valores.items():
        existing = db.execute(
            select(Configuracao).where(Configuracao.chave == chave)
        ).scalar_one_or_none()

        if existing:
            existing.valor = valor
            existing.atualizado_em = now
        else:
            db.add(Configuracao(chave=chave, valor=valor, atualizado_em=now))

    db.commit()

    valores = body.valores

    if "etl_interval_minutes" in valores:
        try:
            reagendar_etl(max(10, int(valores["etl_interval_minutes"])))
        except Exception as e:
            logger.error("Erro ao reagendar ETL: %s", e)

    if "report_day" in valores or "report_time" in valores:
        try:
            dia = _read_or_default(db, "report_day", "fri")
            time_str = _read_or_default(db, "report_time", "18:00")
            hora, minuto = map(int, time_str.split(":"))
            reagendar_relatorio_whatsapp(dia, hora, minuto, _enviar_relatorio_whatsapp)
        except Exception as e:
            logger.error("Erro ao reagendar WhatsApp: %s", e)

    if "report_email_day" in valores or "report_email_time" in valores:
        try:
            dia = _read_or_default(db, "report_email_day", "fri")
            time_str = _read_or_default(db, "report_email_time", "18:00")
            hora, minuto = map(int, time_str.split(":"))
            reagendar_relatorio_email(dia, hora, minuto, _enviar_relatorio_email)
        except Exception as e:
            logger.error("Erro ao reagendar Email: %s", e)

    stmt = select(Configuracao)
    results = db.execute(stmt).scalars().all()
    return ConfiguracaoResponse(
        configuracoes={r.chave: r.valor for r in results}
    )


def _read_or_default(db: Session, key: str, default: str) -> str:
    r = db.execute(
        select(Configuracao).where(Configuracao.chave == key)
    ).scalar_one_or_none()
    return r.valor.strip() if r and r.valor else default


@router.post("/configuracoes/logo", response_model=LogoUploadResponse, status_code=201)
def upload_logo(
    file: UploadFile = File(...),
    _admin: Usuario = Depends(require_admin),
):
    os.makedirs(STATIC_DIR, exist_ok=True)

    ext = os.path.splitext(file.filename or "logo.png")[1] or ".png"
    filename = f"logo{ext}"
    filepath = os.path.join(STATIC_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    logo_url = f"/static/{filename}"

    init_db()
    from app.infrastructure.db.session import SqliteSession
    db = SqliteSession()
    try:
        existing = db.execute(
            select(Configuracao).where(Configuracao.chave == "logo_url")
        ).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if existing:
            existing.valor = logo_url
            existing.atualizado_em = now
        else:
            db.add(Configuracao(chave="logo_url", valor=logo_url, atualizado_em=now))
        db.commit()
    finally:
        db.close()

    return {"logo_url": logo_url}
