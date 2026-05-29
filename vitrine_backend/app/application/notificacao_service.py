"""Serviço de Notificações Internas.

Criação, consulta e resolução de notificações pós-sync.
Cada notificação é CONSOLIDADA — 1 alerta agrega N produtos problemáticos.
"""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.models.notificacao import Notificacao

logger = logging.getLogger(__name__)

MAX_NOTIFICACOES = 200


def criar_notificacao(
    db: Session,
    tipo: str,
    titulo: str,
    mensagem: str | None = None,
    dados_json: dict | None = None,
) -> Notificacao:
    """Cria notificação ou atualiza se já existir uma ABERTA do mesmo tipo.

    Se já existe notificação do mesmo tipo com resolvida=False,
    apenas atualiza o título/mensagem/dados (evita duplicação).
    """
    # Busca notificação aberta do mesmo tipo
    existente = (
        db.query(Notificacao)
        .filter(Notificacao.tipo == tipo, Notificacao.resolvida == False)
        .first()
    )
    if existente:
        existente.titulo = titulo
        existente.mensagem = mensagem
        existente.dados_json = json.dumps(dados_json) if dados_json else None
        existente.lida = False
        existente.resolvida = False
        db.commit()
        logger.info("Notificação atualizada: %s (%s)", tipo, titulo)
        return existente

    notif = Notificacao(
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        dados_json=json.dumps(dados_json) if dados_json else None,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    logger.info("Notificação criada: %s (%s)", tipo, titulo)
    return notif


def listar_notificacoes(db: Session, limit: int = 50, offset: int = 0) -> list[Notificacao]:
    """Lista notificações, não resolvidas primeiro, depois por data desc."""
    return (
        db.query(Notificacao)
        .order_by(Notificacao.resolvida.asc(), Notificacao.criada_em.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def contar_nao_lidas(db: Session) -> int:
    """Quantas notificações abertas e não lidas existem."""
    return (
        db.query(Notificacao)
        .filter(Notificacao.lida == False, Notificacao.resolvida == False)
        .count()
    )


def marcar_como_lida(db: Session, notificacao_id: int) -> Notificacao | None:
    """Marca notificação como lida."""
    notif = db.query(Notificacao).filter(Notificacao.id == notificacao_id).first()
    if notif:
        notif.marcar_lida()
        db.commit()
    return notif


def marcar_todas_como_lidas(db: Session) -> int:
    """Marca todas as não lidas como lidas. Retorna quantas foram afetadas."""
    qtd = (
        db.query(Notificacao)
        .filter(Notificacao.lida == False, Notificacao.resolvida == False)
        .update({"lida": True, "lida_em": datetime.now(timezone.utc).replace(tzinfo=None)})
    )
    db.commit()
    return qtd


def resolver_notificacao(db: Session, tipo: str) -> int:
    """Resolve todas as notificações abertas de um tipo.

    Usado pós-sync: se o problema foi resolvido (ex: margens normalizadas),
    as notificações antigas são marcadas como resolvidas.
    Retorna quantas foram resolvidas.
    """
    qtd = (
        db.query(Notificacao)
        .filter(Notificacao.tipo == tipo, Notificacao.resolvida == False)
        .update({"resolvida": True, "resolvida_em": datetime.now(timezone.utc).replace(tzinfo=None)})
    )
    db.commit()
    return qtd


def limpar_lidas(db: Session, dias: int = 30) -> int:
    """Remove notificações lidas/resolvidas mais antigas que N dias."""
    from datetime import timedelta

    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    qtd = (
        db.query(Notificacao)
        .filter(
            Notificacao.resolvida == True,
            Notificacao.criada_em < limite,
        )
        .delete()
    )
    db.commit()
    return qtd
