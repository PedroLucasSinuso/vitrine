from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.domain.models.cache_status import CacheStatus
from app.domain.models.usuario import Usuario
from app.limiter import limiter

router = APIRouter(prefix="/status", tags=["Status"])


@router.get("/")
@limiter.limit("10/minute")
def get_status(
    request: Request,
    db=Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Status do cache de produtos DA EMPRESA do usuário logado.

    Antes exigia só um TTL/rate-limit e nenhuma autenticação: sem
    escopo de tenant, isso vazava o timestamp de última sincronização
    de qualquer empresa para qualquer visitante não autenticado (e não
    dava pra escopar sem saber quem está perguntando). A única chamada
    real no frontend (Admin.tsx) já é uma página autenticada, então
    exigir login aqui não quebra nenhum uso existente.
    """
    stmt = (
        select(CacheStatus)
        .where(CacheStatus.empresa_id == usuario.empresa_id)
        .order_by(CacheStatus.id.desc())
    )
    result = db.execute(stmt).scalars().first()

    return {
        "last_updated": result.last_updated if result else None
    }
