"""
app/api/routes/inventario.py  — substitui o arquivo existente na íntegra

Mudanças em relação ao original:
  • GET /admin/inventario/sessoes/{id}/exportar-excel  (NOVO)
    Exporta Excel com duas abas:
      - "Contagem"          → dados bipados da sessão (consolidado por código)
      - "Delta (vs. Sistema)" → cruza com estoque atual do SQLite (campo stock de Product)
    Requer role supervisor ou admin.
  • GET /admin/inventario/consolidado-geral/exportar-excel  (NOVO)
    Mesmo formato, mas consolida TODAS as sessões ativas.
  • Todo o resto permanece idêntico ao original.
"""

import io
import secrets
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.reporting.excel_inventario import build_excel_inventario

from app.api.deps import get_db, get_current_user, require_supervisor
from fastapi import status
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
# Produto traz o estoque atual do SQLite
from app.domain.models.produto import Produto

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# ATENÇÃO — Prefixo /admin/ é intencional (ADR-012)
# ────────────────────────────────────────────────────────────────────────────
# O prefixo atual é "/admin/inventario" por razões históricas, mas a maioria
# das rotas usa `get_current_user` (qualquer role autenticado), não
# `require_supervisor`. Isso é DELIBERADO — operadores precisam acessar o
# inventário para contar estoque.
#
# ADR-012: Operadores têm página própria em /inventario (frontend), mas o
# backend mantém as rotas sob /admin/inventario. Supervisores e admins
# também usam estas mesmas rotas.
#
# NÃO "corrija" adicionando role checks desnecessários — operadores precisam
# destes endpoints para trabalhar.
#
# Se no futuro houver separação de roles (ex: admin ≠ supervisor ≠ operador
# com permissões distintas no inventário), mova as rotas de operador para um
# prefixo /inventario e restrinja /admin/inventario.
# ────────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/admin/inventario", tags=["Inventario"])


# ─────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────

def gerar_codigo_convite() -> str:
    return secrets.token_hex(3).upper()


def get_session_or_404(sessao_id: int, db: Session) -> SessaoInventario:
    sessao = db.execute(
        select(SessaoInventario).where(SessaoInventario.id == sessao_id)
    ).scalar_one_or_none()
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return sessao


def require_sessao_ativa(sessao: SessaoInventario) -> None:
    """Levanta 400 se a sessão não estiver ativa.
    
    Chamado pelas rotas que modificam itens (adicionar, listar, atualizar, limpar)
    para impedir operações em sessões encerradas. A rota entrar_sessao faz esta
    verificação diretamente; as demais usam este helper."""
    if sessao.status != "ativa":
        raise HTTPException(status_code=400, detail="Sessão já encerrada")


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


def _consolidar_itens_sessao(sessao_id: int, db: Session) -> list[dict]:
    """Retorna itens consolidados (sum por código) de UMA sessão."""
    rows = db.execute(
        select(
            ItemInventario.codigo,
            ItemInventario.nome,
            ItemInventario.grupo,
            ItemInventario.familia,
            func.sum(ItemInventario.quantidade).label("quantidade"),
        )
        .where(ItemInventario.sessao_id == sessao_id)
        .group_by(
            ItemInventario.codigo,
            ItemInventario.nome,
            ItemInventario.grupo,
            ItemInventario.familia,
        )
    ).all()
    return [
        {"codigo": r.codigo, "nome": r.nome, "grupo": r.grupo,
         "familia": r.familia, "quantidade": int(r.quantidade)}
        for r in rows
    ]


def _consolidar_itens_todas_sessoes(db: Session) -> list[dict]:
    """Retorna itens consolidados de TODAS as sessões ativas."""
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
        .group_by(
            ItemInventario.codigo,
            ItemInventario.nome,
            ItemInventario.grupo,
            ItemInventario.familia,
        )
    ).all()
    return [
        {"codigo": r.codigo, "nome": r.nome, "grupo": r.grupo,
         "familia": r.familia, "quantidade": int(r.quantidade)}
        for r in rows
    ]


def _get_estoque_db(
    codigos: list[str],
    db: Session,
) -> dict[str, float]:
    """
    Busca o estoque atual dos produtos no SQLite.
    Primeiro busca por codigo_chamada (código interno ERP),
    depois tenta por ProdutoCodigo.codigo (EAN / código de barras)
    para os códigos não encontrados.
    Retorna mapa codigo_chamada → estoque.
    Produtos não encontrados ficam ausentes do mapa.
    """
    if not codigos:
        return {}
    try:
        # Passo 1: busca direta por codigo_chamada
        rows = db.execute(
            select(Produto.codigo_chamada, Produto.estoque)
            .where(Produto.codigo_chamada.in_(codigos))
        ).all()
        resultado = {r.codigo_chamada: float(r.estoque) for r in rows}

        # Passo 2: para códigos não encontrados, tenta por ProdutoCodigo (EAN)
        from app.domain.models.produto import ProdutoCodigo
        faltantes = [c for c in codigos if c not in resultado]
        if faltantes:
            ean_rows = db.execute(
                select(Produto.codigo_chamada, Produto.estoque)
                .join(ProdutoCodigo, Produto.codigo_chamada == ProdutoCodigo.codigo_chamada)
                .where(ProdutoCodigo.codigo.in_(faltantes))
            ).all()
            for r in ean_rows:
                resultado[r.codigo_chamada] = float(r.estoque)

        return resultado
    except Exception:
        logger.exception("Falha ao buscar estoque para delta — exportando sem delta")
        return {}


def _upsert_item(
    sessao_id: int,
    usuario_id: int,
    body: ItemInventarioSubmit,
    db: Session,
) -> None:
    """Adiciona ou atualiza um item no inventário (upsert).

    Se o item já existe para o mesmo usuário na mesma sessão (mesmo código),
    incrementa a quantidade e concatena a observação. Caso contrário, cria
    um novo registro.

    Race condition: se dois requests concorrentes baterem no mesmo (sessao,
    usuario, codigo), apenas um vence (IntegrityError no segundo). O código
    então refaz a busca e atualiza o existente. Se a segunda tentativa
    também falhar, retorna HTTP 400 amigável (em vez de 500).
    """

    def _do_upsert() -> None:
        existing = db.execute(
            select(ItemInventario)
            .where(ItemInventario.sessao_id == sessao_id)
            .where(ItemInventario.usuario_id == usuario_id)
            .where(ItemInventario.codigo == body.codigo)
        ).scalar_one_or_none()

        if existing:
            existing.quantidade += body.quantidade
            if body.observacao:
                existing.observacao = (
                    (existing.observacao + " | " + body.observacao)[:500]
                    if existing.observacao
                    else body.observacao
                )
        else:
            db.add(ItemInventario(
                sessao_id=sessao_id,
                usuario_id=usuario_id,
                codigo=body.codigo,
                nome=body.nome,
                grupo=body.grupo,
                familia=body.familia,
                quantidade=body.quantidade,
                observacao=body.observacao or None,
            ))

    try:
        _do_upsert()
        db.commit()
    except IntegrityError:
        db.rollback()
        try:
            # Retry: race condition — outro request inseriu o mesmo item
            _do_upsert()
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conflito ao salvar item. Tente novamente.",
            )


# ─────────────────────────────────────────
# Endpoints existentes (sem alteração)
# ─────────────────────────────────────────

@router.get("/sessoes", response_model=list[SessaoResponse])
def listar_sessoes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    stmt = select(SessaoInventario).where(SessaoInventario.status == "ativa")
    sessoes = db.execute(stmt).scalars().all()
    return [_build_sessao_response(s, db) for s in sessoes]


@router.post("/sessoes", response_model=SessaoResponse, status_code=201)
def criar_sessao(
    body: CriarSessaoInput,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_supervisor),
):
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

    sessao = get_session_or_404(sessao_id, db)

    # Sessões encerradas: operador não pode listar itens (apenas supervisor/admin)
    if sessao.status != "ativa" and usuario.role not in ("supervisor", "admin"):
        raise HTTPException(status_code=403, detail="Sessão encerrada. Apenas supervisor ou admin.")

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
            .group_by(
                ItemInventario.codigo,
                ItemInventario.nome,
                ItemInventario.grupo,
                ItemInventario.familia,
            )
        ).all()
        return [
            ItemInventarioResponse(
                codigo=r.codigo, nome=r.nome, grupo=r.grupo,
                familia=r.familia, quantidade=r.quantidade,
            )
            for r in rows
        ]

    rows = db.execute(
        select(ItemInventario)
        .where(ItemInventario.sessao_id == sessao_id)
        .where(ItemInventario.usuario_id == usuario.id)
    ).scalars().all()
    return [
        ItemInventarioResponse(
            codigo=r.codigo, nome=r.nome, grupo=r.grupo,
            familia=r.familia, quantidade=r.quantidade,
            observacao=r.observacao or "",
        )
        for r in rows
    ]


@router.post("/sessoes/{sessao_id}/itens", status_code=201)
def adicionar_item(
    sessao_id: int,
    body: ItemInventarioSubmit,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):

    sessao = get_session_or_404(sessao_id, db)
    require_sessao_ativa(sessao)

    _upsert_item(sessao_id, usuario.id, body, db)

    return {"ok": True}


@router.get("/consolidado-geral", response_model=list[ItemInventarioResponse])
def consolidado_geral(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_supervisor),
):

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
        .group_by(
            ItemInventario.codigo,
            ItemInventario.nome,
            ItemInventario.grupo,
            ItemInventario.familia,
        )
    ).all()
    return [
        ItemInventarioResponse(
            codigo=r.codigo, nome=r.nome, grupo=r.grupo,
            familia=r.familia, quantidade=r.quantidade,
        )
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

    sessao = get_session_or_404(sessao_id, db)
    require_sessao_ativa(sessao)

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
        if body.observacao is not None:
            item.observacao = body.observacao or None

    db.commit()
    return {"ok": True}


@router.delete("/sessoes/{sessao_id}/itens")
def limpar_itens(
    sessao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):

    sessao = get_session_or_404(sessao_id, db)
    require_sessao_ativa(sessao)

    db.execute(
        delete(ItemInventario)
        .where(ItemInventario.sessao_id == sessao_id)
        .where(ItemInventario.usuario_id == usuario.id)
    )
    db.commit()
    return {"ok": True}


# ─────────────────────────────────────────
# NOVOS endpoints de exportação Excel
# ─────────────────────────────────────────

@router.get("/sessoes/{sessao_id}/exportar-excel")
def exportar_excel_sessao(
    sessao_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_supervisor),
):
    """
    Exporta Excel de UMA sessão (consolidado de todos os operadores).
    Aba "Contagem"           → itens bipados, somados por código.
    Aba "Delta (vs. Sistema)" → cruza com estoque atual do SQLite.
    Apenas supervisores e admins.
    """

    sessao = get_session_or_404(sessao_id, db)

    itens = _consolidar_itens_sessao(sessao_id, db)
    if not itens:
        raise HTTPException(status_code=404, detail="Nenhum item nesta sessão")

    codigos = [i["codigo"] for i in itens]
    estoque_db = _get_estoque_db(codigos, db)

    # Observações desta sessão
    obs_rows = db.execute(
        select(ItemInventario.codigo, ItemInventario.nome, ItemInventario.observacao)
        .where(ItemInventario.sessao_id == sessao_id)
        .where(ItemInventario.observacao.isnot(None))
        .where(ItemInventario.observacao != "")
    ).all()
    observacoes = [{"codigo": r.codigo, "nome": r.nome, "observacao": r.observacao} for r in obs_rows]

    nome = sessao.nome or f"sessao_{sessao_id}"
    nome_arquivo = f"inventario_{nome}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    nome_arquivo = "".join(c for c in nome_arquivo if c.isalnum() or c in "-_.")

    excel_bytes = build_excel_inventario(itens, estoque_db, nome, observacoes)

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_arquivo}"',
            "Content-Length": str(len(excel_bytes)),
        },
    )


@router.get("/consolidado-geral/exportar-excel")
def exportar_excel_consolidado_geral(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_supervisor),
):
    """
    Exporta Excel consolidado de TODAS as sessões ativas.
    Mesmo formato de duas abas.
    """

    itens = _consolidar_itens_todas_sessoes(db)
    if not itens:
        raise HTTPException(status_code=404, detail="Nenhum item nas sessões ativas")

    codigos = [i["codigo"] for i in itens]
    estoque_db = _get_estoque_db(codigos, db)

    # Observações de todas as sessões ativas
    obs_rows = db.execute(
        select(ItemInventario.codigo, ItemInventario.nome, ItemInventario.observacao)
        .join(SessaoInventario, ItemInventario.sessao_id == SessaoInventario.id)
        .where(SessaoInventario.status == "ativa")
        .where(ItemInventario.observacao.isnot(None))
        .where(ItemInventario.observacao != "")
    ).all()
    observacoes = [{"codigo": r.codigo, "nome": r.nome, "observacao": r.observacao} for r in obs_rows]

    nome_arquivo = f"inventario_consolidado_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    excel_bytes = build_excel_inventario(itens, estoque_db, "Consolidado Geral", observacoes)

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_arquivo}"',
            "Content-Length": str(len(excel_bytes)),
        },
    )
