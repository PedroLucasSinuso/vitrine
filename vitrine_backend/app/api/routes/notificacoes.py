"""Rotas de Notificações Internas.

Acessível por supervisores e admins.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_supervisor
from app.application.notificacao_service import (
    contar_nao_lidas,
    criar_notificacao,
    limpar_lidas,
    listar_notificacoes,
    marcar_como_lida,
    marcar_todas_como_lidas,
    resolver_notificacao,
)
from app.domain.models.usuario import Usuario
from app.limiter import limiter
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])


class NotificacaoResponse(BaseModel):
    id: int
    tipo: str
    titulo: str
    mensagem: str | None = None
    dados_json: str | None = None
    lida: bool
    resolvida: bool
    criada_em: str
    lida_em: str | None = None
    resolvida_em: str | None = None


class NotificacaoListResponse(BaseModel):
    notificacoes: list[NotificacaoResponse]
    total_nao_lidas: int


def _to_response(n: object) -> NotificacaoResponse:
    """Converte modelo ORM para schema Pydantic."""
    return NotificacaoResponse(
        id=n.id,
        tipo=n.tipo,
        titulo=n.titulo,
        mensagem=n.mensagem,
        dados_json=n.dados_json,
        lida=n.lida,
        resolvida=n.resolvida,
        criada_em=n.criada_em.isoformat() if n.criada_em else "",
        lida_em=n.lida_em.isoformat() if n.lida_em else None,
        resolvida_em=n.resolvida_em.isoformat() if n.resolvida_em else None,
    )


@router.get("", response_model=NotificacaoListResponse)
@limiter.limit("30/minute")
def get_notificacoes(
    request: Request,
    db: Session = Depends(get_db),
    _user: Usuario = Depends(require_supervisor),
    limit: int = 50,
    offset: int = 0,
):
    """Lista notificações (não resolvidas primeiro)."""
    notificacoes = listar_notificacoes(db, limit=limit, offset=offset)
    total = contar_nao_lidas(db)
    return NotificacaoListResponse(
        notificacoes=[_to_response(n) for n in notificacoes],
        total_nao_lidas=total,
    )


@router.get("/nao-lidas")
@limiter.limit("30/minute")
def get_nao_lidas(
    request: Request,
    db: Session = Depends(get_db),
    _user: Usuario = Depends(require_supervisor),
):
    """Retorna apenas o count de notificações não lidas (para o badge)."""
    return {"count": contar_nao_lidas(db)}


@router.patch("/{notificacao_id}/ler")
@limiter.limit("30/minute")
def patch_ler(
    request: Request,
    notificacao_id: int,
    db: Session = Depends(get_db),
    _user: Usuario = Depends(require_supervisor),
):
    """Marca notificação como lida."""
    notif = marcar_como_lida(db, notificacao_id)
    if not notif:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    return _to_response(notif)


@router.post("/ler-todas")
@limiter.limit("10/minute")
def post_ler_todas(
    request: Request,
    db: Session = Depends(get_db),
    _user: Usuario = Depends(require_supervisor),
):
    """Marca todas as notificações como lidas."""
    qtd = marcar_todas_como_lidas(db)
    return {"marcadas": qtd}


@router.post("/limpar")
@limiter.limit("10/minute")
def post_limpar(
    request: Request,
    db: Session = Depends(get_db),
    _user: Usuario = Depends(require_supervisor),
    dias: int = 30,
):
    """Remove notificações resolvidas mais antigas que N dias."""
    qtd = limpar_lidas(db, dias=dias)
    return {"removidas": qtd}
