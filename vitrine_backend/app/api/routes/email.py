from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.domain.models.email_contato import EmailContato
from app.schemas.email_schema import EmailContatoCreate, EmailContatoUpdate, EmailContatoResponse
from app.infrastructure.db.bootstrap import init_db
from app.domain.models.usuario import Usuario
from app.api.deps import require_supervisor, require_admin

router = APIRouter(prefix="/admin/email", tags=["email"])


@router.get("/contatos", response_model=list[EmailContatoResponse])
def listar_contatos(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_supervisor),
):
    init_db()
    stmt = select(EmailContato).order_by(EmailContato.nome)
    return db.execute(stmt).scalars().all()


@router.post("/contatos", response_model=EmailContatoResponse, status_code=201)
def criar_contato(
    body: EmailContatoCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_supervisor),
):
    init_db()
    contato = EmailContato(email=body.email, nome=body.nome)
    db.add(contato)
    db.commit()
    db.refresh(contato)
    return contato


@router.put("/contatos/{contato_id}", response_model=EmailContatoResponse)
def atualizar_contato(
    contato_id: int,
    body: EmailContatoUpdate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_supervisor),
):
    contato = db.execute(
        select(EmailContato).where(EmailContato.id == contato_id)
    ).scalar_one_or_none()
    if not contato:
        from fastapi import HTTPException
        raise HTTPException(404, "Contato não encontrado")
    contato.email = body.email
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
        select(EmailContato).where(EmailContato.id == contato_id)
    ).scalar_one_or_none()
    if not contato:
        from fastapi import HTTPException
        raise HTTPException(404, "Contato não encontrado")
    db.delete(contato)
    db.commit()


@router.post("/teste")
def testar_email(
    _admin: Usuario = Depends(require_admin),
):
    from app.application.notifications.scheduler_notifications import _enviar_relatorio_email
    _enviar_relatorio_email()
    return {"ok": True, "mensagem": "Relatório de teste enviado por email"}
