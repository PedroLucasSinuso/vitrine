"""Macro-economic indicators endpoint — live data from Banco Central do Brasil."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.limiter import limiter

router = APIRouter(prefix="/bi/intelligence", tags=["Intelligence"])


@router.get("/macro")
@limiter.limit("30/hour")
async def get_macro_indicators(
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """Returns current macro indicators with availability + timestamps.

    Rate limited: 30/hour (same as intelligence analysis endpoint).
    No auth required (same pattern as /bi/intelligence/debug).
    """
    from app.application.intelligence.macro_fetcher import fetch_todos_indicadores

    indicadores = await fetch_todos_indicadores(db)

    return [
        {
            "chave": v.chave,
            "rotulo": v.rotulo,
            "valor": v.valor,
            "disponivel": v.disponivel,
            "unidade": v.unidade,
            "periodo_ref": v.periodo_ref_rotulo,
            "consultado_em": v.consultado_em.isoformat(),
            "mensagem": v.mensagem,
        }
        for v in indicadores.values()
    ]
