from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_empresa_do_usuario, get_fonte_equipe, require_modulo, require_supervisor
from app.application.equipe.fonte import FonteEquipe
from app.application.equipe.metas import aliases_da_empresa, metas_para_calculo
from app.domain.models.empresa import Empresa
from vitrine_core.bi.equipe import competencia_do_periodo
from app.application.equipe.servico import IndicadorIndisponivel, grade, mix, resultado_equipe, serie
from app.limiter import limiter
from vitrine_core.bi.equipe import ItemMixVendedor, PontoSerieVendedor, ResultadoEquipe
from vitrine_core.bi.grade import ResultadoGrade

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
    empresa: Empresa = Depends(get_empresa_do_usuario),
    db: Session = Depends(get_db),
):
    inicio, fim = _periodo(data_inicio, data_fim)
    return resultado_equipe(
        fonte, inicio, fim,
        metas=metas_para_calculo(db, empresa.id, competencia_do_periodo(inicio, fim)),
        aliases=aliases_da_empresa(db, empresa.id),
    )


@router.get("/serie", response_model=list[PontoSerieVendedor])
@limiter.limit("20/minute")
def serie_vendedor(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    vendedor: str | None = Query(None),
    fonte: FonteEquipe = Depends(get_fonte_equipe),
    empresa: Empresa = Depends(get_empresa_do_usuario),
    db: Session = Depends(get_db),
):
    try:
        return serie(fonte, *_periodo(data_inicio, data_fim), vendedor, aliases_da_empresa(db, empresa.id))
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
    empresa: Empresa = Depends(get_empresa_do_usuario),
    db: Session = Depends(get_db),
):
    try:
        return mix(fonte, *_periodo(data_inicio, data_fim), vendedor, aliases_da_empresa(db, empresa.id))
    except IndicadorIndisponivel as erro:
        raise HTTPException(status_code=409, detail=str(erro))


router_grade = APIRouter(
    prefix="/bi/grade",
    tags=["BI - Grade"],
    dependencies=[Depends(require_supervisor), Depends(require_modulo("grade"))],
)


@router_grade.get("", response_model=ResultadoGrade)
@limiter.limit("20/minute")
def grade_de_vendas(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    grupo: str | None = Query(None),
    familia: str | None = Query(None),
    fonte: FonteEquipe = Depends(get_fonte_equipe),
):
    try:
        return grade(fonte, *_periodo(data_inicio, data_fim), grupo, familia)
    except IndicadorIndisponivel as erro:
        raise HTTPException(status_code=409, detail=str(erro))
