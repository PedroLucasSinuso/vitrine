import secrets
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_supervisor
from app.schemas.inventario_schema import (
    CriarSessaoInput,
    EntrarSessaoInput,
    SessaoResponse,
    ItemInventarioSubmit,
    ItemInventarioResponse,
    AtualizarItemInput,
)
from app.domain.models.inventario import SessaoInventario, ItemInventario
from app.domain.models.usuario import Usuario
from app.infrastructure.db.bootstrap import init_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/inventario", tags=["Inventario"])


def gerar_codigo_convite() -> str:
    return secrets.token_hex(3).upper()


def get_session_or_404(sessao_id: int, db: Session) -> SessaoInventario:
    sessao = db.execute(
        select(SessaoInventario).where(SessaoInventario.id == sessao_id)
    ).scalar_one_or_none()
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return sessao


def _build_sessao_response(sessao: SessaoInventario, db: Session) -> SessaoResponse:
    total_operadores = db.execute(
        select(func.count(func.distinct(ItemInventario.usuario_id)))
        .where(ItemInventario.sessao_id == sessao.id)
    ).scalar() or 0

    total_itens = db.execute(
        select(func.count(ItemInventario.id))
        .where(ItemInventario.sessao_id == sessao.id)
    ).scalar() or 0

    criador = db.execute(
        select(Usuario).where(Usuario.id == sessao.criado_por_id)
    ).scalar_one_or_none()

    return SessaoResponse(
        id=sessao.id,
        nome=sessao.nome,
        status=sessao.status,
        codigo_convite=sessao.codigo_convite,
        criado_por=criador.username if criador else "?",
        criado_em=sessao.criado_em,
        total_operadores=total_operadores,
        total_itens=total_itens,
    )


@router.get("/sessoes", response_model=list[SessaoResponse])
def listar_sessoes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    init_db()
    stmt = select(SessaoInventario).where(SessaoInventario.status == "ativa")
    sessoes = db.execute(stmt).scalars().all()
    return [_build_sessao_response(s, db) for s in sessoes]


@router.post("/sessoes", response_model=SessaoResponse, status_code=201)
def criar_sessao(
    body: CriarSessaoInput,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_supervisor),
):
    init_db()
    codigo = gerar_codigo_convite()
    while db.execute(
        select(SessaoInventario).where(SessaoInventario.codigo_convite == codigo)
    ).scalar_one_or_none():
        codigo = gerar_codigo_convite()

    sessao = SessaoInventario(
        nome=body.nome,
        criado_por_id=usuario.id,
        status="ativa",
        codigo_convite=codigo,
        criado_em=datetime.now(timezone.utc),
    )
    db.add(sessao)
    db.commit()
    db.refresh(sessao)
    return _build_sessao_response(sessao, db)


@router.post("/sessoes/entrar", response_model=SessaoResponse, status_code=201)
def entrar_sessao(
    body: EntrarSessaoInput,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    init_db()
    sessao = db.execute(
        select(SessaoInventario).where(SessaoInventario.codigo_convite == body.codigo_convite)
    ).scalar_one_or_none()
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if sessao.status != "ativa":
        raise HTTPException(status_code=400, detail="Sessão já encerrada")
    return _build_sessao_response(sessao, db)


@router.patch("/sessoes/{sessao_id}", response_model=SessaoResponse)
def encerrar_sessao(
    sessao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_supervisor),
):
    init_db()
    sessao = get_session_or_404(sessao_id, db)
    if sessao.criado_por_id != usuario.id:
        raise HTTPException(status_code=403, detail="Apenas o criador pode encerrar a sessão")
    sessao.status = "encerrada"
    sessao.encerrado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sessao)
    return _build_sessao_response(sessao, db)


@router.get("/sessoes/{sessao_id}/itens", response_model=list[ItemInventarioResponse])
def listar_itens(
    sessao_id: int,
    consolidado: bool = False,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    init_db()
    get_session_or_404(sessao_id, db)

    if consolidado and usuario.role in ("supervisor", "admin"):
        rows = db.execute(
            select(
                ItemInventario.codigo,
                ItemInventario.nome,
                ItemInventario.grupo,
                ItemInventario.familia,
                func.sum(ItemInventario.quantidade).label("quantidade"),
            )
            .where(ItemInventario.sessao_id == sessao_id)
            .group_by(ItemInventario.codigo, ItemInventario.nome, ItemInventario.grupo, ItemInventario.familia)
        ).all()
        return [
            ItemInventarioResponse(codigo=r.codigo, nome=r.nome, grupo=r.grupo, familia=r.familia, quantidade=r.quantidade)
            for r in rows
        ]

    rows = db.execute(
        select(ItemInventario)
        .where(ItemInventario.sessao_id == sessao_id)
        .where(ItemInventario.usuario_id == usuario.id)
    ).scalars().all()
    return [
        ItemInventarioResponse(codigo=r.codigo, nome=r.nome, grupo=r.grupo, familia=r.familia, quantidade=r.quantidade)
        for r in rows
    ]


@router.post("/sessoes/{sessao_id}/itens", status_code=201)
def adicionar_item(
    sessao_id: int,
    body: ItemInventarioSubmit,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    init_db()
    get_session_or_404(sessao_id, db)

    try:
        existing = db.execute(
            select(ItemInventario)
            .where(ItemInventario.sessao_id == sessao_id)
            .where(ItemInventario.usuario_id == usuario.id)
            .where(ItemInventario.codigo == body.codigo)
        ).scalar_one_or_none()

        if existing:
            existing.quantidade += body.quantidade
        else:
            item = ItemInventario(
                sessao_id=sessao_id,
                usuario_id=usuario.id,
                codigo=body.codigo,
                nome=body.nome,
                grupo=body.grupo,
                familia=body.familia,
                quantidade=body.quantidade,
            )
            db.add(item)

        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.execute(
            select(ItemInventario)
            .where(ItemInventario.sessao_id == sessao_id)
            .where(ItemInventario.usuario_id == usuario.id)
            .where(ItemInventario.codigo == body.codigo)
        ).scalar_one_or_none()
        if existing:
            existing.quantidade += body.quantidade
        else:
            item = ItemInventario(
                sessao_id=sessao_id,
                usuario_id=usuario.id,
                codigo=body.codigo,
                nome=body.nome,
                grupo=body.grupo,
                familia=body.familia,
                quantidade=body.quantidade,
            )
            db.add(item)
        db.commit()

    return {"ok": True}


@router.get("/consolidado-geral", response_model=list[ItemInventarioResponse])
def consolidado_geral(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_supervisor),
):
    init_db()
    rows = db.execute(
        select(
            ItemInventario.codigo,
            ItemInventario.nome,
            ItemInventario.grupo,
            ItemInventario.familia,
            func.sum(ItemInventario.quantidade).label("quantidade"),
        )
        .join(SessaoInventario, ItemInventario.sessao_id == SessaoInventario.id)
        .where(SessaoInventario.status == "ativa")
        .group_by(ItemInventario.codigo, ItemInventario.nome, ItemInventario.grupo, ItemInventario.familia)
    ).all()
    return [
        ItemInventarioResponse(codigo=r.codigo, nome=r.nome, grupo=r.grupo, familia=r.familia, quantidade=r.quantidade)
        for r in rows
    ]


@router.patch("/sessoes/{sessao_id}/itens/{codigo}")
def atualizar_item(
    sessao_id: int,
    codigo: str,
    body: AtualizarItemInput,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    init_db()
    get_session_or_404(sessao_id, db)

    item = db.execute(
        select(ItemInventario)
        .where(ItemInventario.sessao_id == sessao_id)
        .where(ItemInventario.usuario_id == usuario.id)
        .where(ItemInventario.codigo == codigo)
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    if body.quantidade <= 0:
        db.delete(item)
    else:
        item.quantidade = body.quantidade

    db.commit()
    return {"ok": True}


@router.delete("/sessoes/{sessao_id}/itens")
def limpar_itens(
    sessao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    init_db()
    get_session_or_404(sessao_id, db)

    db.execute(
        delete(ItemInventario)
        .where(ItemInventario.sessao_id == sessao_id)
        .where(ItemInventario.usuario_id == usuario.id)
    )
    db.commit()
    return {"ok": True}
