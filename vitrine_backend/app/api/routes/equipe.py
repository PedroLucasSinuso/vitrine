from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import get_fonte_equipe, require_modulo, require_supervisor
from app.application.equipe.fonte import FonteEquipe
from app.application.equipe.servico import IndicadorIndisponivel, mix, resultado_equipe, serie
from app.limiter import limiter
from vitrine_core.bi.equipe import ItemMixVendedor, PontoSerieVendedor, ResultadoEquipe

router = APIRouter(
    prefix="/bi/equipe",
    tags=["BI - Equipe"],
    dependencies=[Depends(require_supervisor), Depends(require_modulo("equipe"))],
)

MAX_DIAS = 180


def _periodo(data_inicio: date, data_fim: date) -> tuple[date, date]:
    if data_fim < data_inicio:
        raise HTTPException(status_code=400, detail="data_fim não pode ser anterior a data_inicio")
    if (data_fim - data_inicio).days > MAX_DIAS:
        raise HTTPException(status_code=400, detail=f"Período máximo permitido é {MAX_DIAS} dias")
    return data_inicio, data_fim


@router.get("", response_model=ResultadoEquipe)
@limiter.limit("20/minute")
def equipe(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    fonte: FonteEquipe = Depends(get_fonte_equipe),
):
    return resultado_equipe(fonte, *_periodo(data_inicio, data_fim))


@router.get("/serie", response_model=list[PontoSerieVendedor])
@limiter.limit("20/minute")
def serie_vendedor(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    vendedor: str | None = Query(None),
    fonte: FonteEquipe = Depends(get_fonte_equipe),
):
    try:
        return serie(fonte, *_periodo(data_inicio, data_fim), vendedor)
    except IndicadorIndisponivel as erro:
        raise HTTPException(status_code=409, detail=str(erro))


@router.get("/mix", response_model=list[ItemMixVendedor])
@limiter.limit("20/minute")
def mix_vendedor(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    vendedor: str | None = Query(None),
    fonte: FonteEquipe = Depends(get_fonte_equipe),
):
    try:
        return mix(fonte, *_periodo(data_inicio, data_fim), vendedor)
    except IndicadorIndisponivel as erro:
        raise HTTPException(status_code=409, detail=str(erro))
