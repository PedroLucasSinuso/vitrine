from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.domain.models.whatsapp_contato import WhatsAppContato
from app.schemas.whatsapp_schema import WhatsAppContatoCreate, WhatsAppContatoResponse, WhatsAppContatoUpdate
from app.infrastructure.db.bootstrap import init_db
from app.domain.models.usuario import Usuario
from app.api.deps import require_supervisor, require_admin

router = APIRouter(prefix="/admin/whatsapp", tags=["whatsapp"])


@router.get("/contatos", response_model=list[WhatsAppContatoResponse])
def listar_contatos(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_supervisor),
):
    init_db()
    stmt = select(WhatsAppContato).order_by(WhatsAppContato.nome)
    return db.execute(stmt).scalars().all()


@router.post("/contatos", response_model=WhatsAppContatoResponse, status_code=201)
def criar_contato(
    body: WhatsAppContatoCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_supervisor),
):
    init_db()
    contato = WhatsAppContato(numero=body.numero, nome=body.nome)
    db.add(contato)
    db.commit()
    db.refresh(contato)
    return contato


@router.put("/contatos/{contato_id}", response_model=WhatsAppContatoResponse)
def atualizar_contato(
    contato_id: int,
    body: WhatsAppContatoUpdate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_supervisor),
):
    contato = db.execute(
        select(WhatsAppContato).where(WhatsAppContato.id == contato_id)
    ).scalar_one_or_none()
    if not contato:
        from fastapi import HTTPException
        raise HTTPException(404, "Contato não encontrado")
    contato.numero = body.numero
    contato.nome = body.nome
    db.commit()
    db.refresh(contato)
    return contato


@router.delete("/contatos/{contato_id}", status_code=204)
def remover_contato(
    contato_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_supervisor),
):
    contato = db.execute(
        select(WhatsAppContato).where(WhatsAppContato.id == contato_id)
    ).scalar_one_or_none()
    if not contato:
        from fastapi import HTTPException
        raise HTTPException(404, "Contato não encontrado")
    db.delete(contato)
    db.commit()


@router.post("/teste")
def testar_whatsapp(
    _admin: Usuario = Depends(require_admin),
):
    from app.application.notifications.scheduler_notifications import _enviar_relatorio
    _enviar_relatorio()
    return {"ok": True, "mensagem": "Relatório de teste enviado"}
