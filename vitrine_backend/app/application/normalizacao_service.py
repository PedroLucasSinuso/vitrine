"""Serviço de normalização de grupos e famílias de produtos.

Permite configurar mapeamentos de grupo/família originais (crus do ERP)
para valores normalizados. Útil quando o ERP envia variações do mesmo
grupo (ex: "BEBIDAS", "Bebidas", "bebidas") e o operador quer consolidar.

A normalização é aplicada no momento da leitura (query time via
``normalizar()``) ou pode ser integrada no fluxo de ETL futuramente.

NOTA: A normalização é aplicada no SyncService._to_orm() durante o sync.
"""

import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.models.grupo_familia import GrupoFamilia

logger = logging.getLogger(__name__)

# Cache simples para evitar lookup repetido na mesma requisição
_cache_normalizacao: dict[tuple[str, str], tuple[str, str]] = {}


def normalizar(db: Session, grupo: str, familia: str) -> tuple[str, str]:
    """Retorna (grupo_normalizado, familia_normalizada).

    Se existir mapeamento na tabela ``grupos_familias``, retorna os
    valores normalizados. Caso contrário, retorna os originais.
    """
    chave = (grupo, familia)

    # Tenta cache local (mesma requisição)
    if chave in _cache_normalizacao:
        return _cache_normalizacao[chave]

    # Busca no banco
    row = db.execute(
        select(GrupoFamilia).where(
            GrupoFamilia.grupo_original == grupo,
            GrupoFamilia.familia_original == familia,
        )
    ).scalar_one_or_none()

    if row:
        resultado = (row.grupo_normalizado, row.familia_normalizada)
    else:
        resultado = (grupo, familia)

    _cache_normalizacao[chave] = resultado
    return resultado


def adicionar_mapeamento(
    db: Session,
    grupo_original: str,
    familia_original: str,
    grupo_normalizado: str,
    familia_normalizada: str,
) -> GrupoFamilia:
    """Cria ou atualiza um mapeamento de normalização.

    Se já existir um mapeamento para (grupo_original, familia_original),
    atualiza os valores normalizados. Caso contrário, cria um novo.

    Retorna a instância ``GrupoFamilia`` persistida.
    """
    row = db.execute(
        select(GrupoFamilia).where(
            GrupoFamilia.grupo_original == grupo_original,
            GrupoFamilia.familia_original == familia_original,
        )
    ).scalar_one_or_none()

    if row:
        row.grupo_normalizado = grupo_normalizado
        row.familia_normalizada = familia_normalizada
        logger.info(
            "Mapeamento atualizado | %s/%s → %s/%s",
            grupo_original, familia_original, grupo_normalizado, familia_normalizada,
        )
    else:
        row = GrupoFamilia(
            grupo_original=grupo_original,
            familia_original=familia_original,
            grupo_normalizado=grupo_normalizado,
            familia_normalizada=familia_normalizada,
        )
        db.add(row)
        logger.info(
            "Mapeamento criado | %s/%s → %s/%s",
            grupo_original, familia_original, grupo_normalizado, familia_normalizada,
        )

    db.commit()
    _cache_normalizacao.clear()
    return row


def listar_mapeamentos(db: Session) -> list[GrupoFamilia]:
    """Retorna todos os mapeamentos cadastrados."""
    return list(
        db.execute(select(GrupoFamilia).order_by(GrupoFamilia.grupo_original)).scalars().all()
    )


def remover_mapeamento(db: Session, mapeamento_id: int) -> bool:
    """Remove um mapeamento pelo ID. Retorna True se removeu."""
    row = db.execute(
        select(GrupoFamilia).where(GrupoFamilia.id == mapeamento_id)
    ).scalar_one_or_none()
    if not row:
        return False
    db.delete(row)
    db.commit()
    _cache_normalizacao.clear()
    logger.info("Mapeamento removido | id=%s", mapeamento_id)
    return True


def invalidar_cache_normalizacao() -> None:
    """Limpa o cache de normalização."""
    _cache_normalizacao.clear()
