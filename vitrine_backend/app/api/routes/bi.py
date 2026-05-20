from datetime import date, datetime
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from app.limiter import limiter
from app.api.deps import get_db, require_supervisor, get_transaction_source
from app.domain.models.usuario import Usuario
from app.core.interfaces.source import TransactionSource
from sqlalchemy.orm import Session
from app.application.bi.factory import criar_dominio, criar_dominio_comparativo
from app.application.bi.domain.perdas import Perdas
from app.application.bi.domain.consumo import Consumo
from app.application.bi.reporting.relatorio import Relatorio, comparar_kpis
from app.application.bi.reporting.relatorio_diario import RelatorioDiario
from app.application.bi.reporting.relatorio_temporal import RelatorioTemporal
from app.application.bi.reporting.relatorio_sku import RelatorioSku
from app.application.bi.reporting.relatorio_movimento import RelatorioMovimento
from app.application.bi.schema import Dimensao, Metrica
from app.schemas.bi_schema import (
    KpisDTO,
    KpisComparativoDTO,
    ItemDimensaoDTO,
    ItemCurvaAbcDTO,
    ItemRankingDTO,
    TrocasDTO,
    MovimentoDTO,
    PontoDiarioDTO,
    PontoHoraDTO,
    PontoDiaSemanaDTO,
    SkuDTO,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bi", tags=["BI"])


def _periodo(data_inicio: date, data_fim: date, comparar: bool = False) -> tuple[date, date]:
    if data_fim < data_inicio:
        raise HTTPException(status_code=400, detail="data_fim não pode ser anterior a data_inicio")
    max_dias = 731 if comparar else 366
    if (data_fim - data_inicio).days > max_dias:
        raise HTTPException(status_code=400, detail=f"Range máximo permitido é {max_dias} dias")
    return data_inicio, data_fim


# ── KPIs ──────────────────────────────────────────────────────────────────────

@router.get("/kpis", response_model=KpisDTO)
@limiter.limit("20/minute")
def kpis(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Calcula e retorna os KPIs de vendas e trocas para o período informado."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | kpis periodo=%s..%s", data_inicio, data_fim)
    dominio = criar_dominio(source, data_inicio, data_fim)
    return Relatorio(dominio.vendas, dominio.trocas).kpis()


@router.get("/kpis/comparativo", response_model=KpisComparativoDTO)
@limiter.limit("20/minute")
def kpis_comparativo(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    data_inicio, data_fim = _periodo(data_inicio, data_fim, comparar=True)
    logger.info("BI Request | kpis/comparativo periodo=%s..%s", data_inicio, data_fim)
    dominio_atual, dominio_anterior = criar_dominio_comparativo(source, data_inicio, data_fim)
    kpis_atual = Relatorio(dominio_atual.vendas, dominio_atual.trocas).kpis()
    kpis_anterior = (
        Relatorio(dominio_anterior.vendas, dominio_anterior.trocas).kpis()
        if dominio_anterior else None
    )
    dados_parciais_ate = None
    if data_fim == date.today():
        dados_parciais_ate = datetime.now().strftime("%H:%M")
    return comparar_kpis(kpis_atual, kpis_anterior, dados_parciais_ate)


# ── Receita e Quantidade por Dimensão ─────────────────────────────────────────

@router.get("/receita", response_model=list[ItemDimensaoDTO])
@limiter.limit("20/minute")
def receita_por_dimensao(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    dimensao: Dimensao = Query(Dimensao.PRODUTO),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna a receita agregada por dimensão (produto, grupo, família) no período."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | receita periodo=%s..%s dimensao=%s", data_inicio, data_fim, dimensao.value)
    dominio = criar_dominio(source, data_inicio, data_fim)
    return Relatorio(dominio.vendas, dominio.trocas).por_dimensao(dimensao, Metrica.RECEITA)


@router.get("/quantidade", response_model=list[ItemDimensaoDTO])
@limiter.limit("20/minute")
def quantidade_por_dimensao(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    dimensao: Dimensao = Query(Dimensao.PRODUTO),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna a quantidade vendida agregada por dimensão no período."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | quantidade periodo=%s..%s dimensao=%s", data_inicio, data_fim, dimensao.value)
    dominio = criar_dominio(source, data_inicio, data_fim)
    return Relatorio(dominio.vendas, dominio.trocas).por_dimensao(dimensao, Metrica.QUANTIDADE)


@router.get("/curva-abc", response_model=list[ItemCurvaAbcDTO])
@limiter.limit("20/minute")
def curva_abc(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    dimensao: Dimensao = Query(Dimensao.PRODUTO),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Gera a curva ABC de produtos baseada na receita no período informado."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | curva-abc periodo=%s..%s dimensao=%s", data_inicio, data_fim, dimensao.value)
    dominio = criar_dominio(source, data_inicio, data_fim)
    return Relatorio(dominio.vendas, dominio.trocas).curva_abc(dimensao)


@router.get("/ranking", response_model=list[ItemRankingDTO])
@limiter.limit("20/minute")
def ranking(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    metrica: Metrica = Query(Metrica.RECEITA),
    top: int = Query(default=10, ge=1, le=100),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna o ranking de produtos por métrica (receita ou quantidade) no período."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | ranking periodo=%s..%s metrica=%s top=%s", data_inicio, data_fim, metrica.value, top)
    dominio = criar_dominio(source, data_inicio, data_fim)
    return Relatorio(dominio.vendas, dominio.trocas).ranking(metrica, top)


@router.get("/trocas", response_model=TrocasDTO)
@limiter.limit("20/minute")
def trocas(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna o resumo de trocas (devoluções) com métricas e breakdown por produto."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | trocas periodo=%s..%s", data_inicio, data_fim)
    dominio = criar_dominio(source, data_inicio, data_fim)
    return Relatorio(dominio.vendas, dominio.trocas).trocas_resumo()


# ── Perdas ────────────────────────────────────────────────────────────────────

@router.get("/perdas", response_model=MovimentoDTO)
@limiter.limit("20/minute")
def perdas(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna o resumo de perdas (quebras de estoque) no período informado."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | perdas periodo=%s..%s", data_inicio, data_fim)
    items = source.get_items(data_inicio, data_fim)
    return RelatorioMovimento(Perdas(items)).resumo()


@router.get("/consumo", response_model=MovimentoDTO)
@limiter.limit("20/minute")
def consumo(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna o resumo de consumo interno (uso próprio) no período informado."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | consumo periodo=%s..%s", data_inicio, data_fim)
    items = source.get_items(data_inicio, data_fim)
    return RelatorioMovimento(Consumo(items)).resumo()


# ── Série Diária ──────────────────────────────────────────────────────────────

@router.get("/diario", response_model=list[PontoDiarioDTO])
@limiter.limit("20/minute")
def serie_diaria(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    metrica: Metrica = Query(Metrica.RECEITA),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna a série temporal diária de vendas para o período informado."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | diario periodo=%s..%s metrica=%s", data_inicio, data_fim, metrica.value)
    dominio = criar_dominio(source, data_inicio, data_fim)
    return RelatorioDiario(dominio.vendas).serie_temporal(metrica)


@router.get("/diario/produto", response_model=list[PontoDiarioDTO])
@limiter.limit("20/minute")
def serie_diaria_produto(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    codigo: str = Query(...),
    metrica: Metrica = Query(Metrica.RECEITA),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna a série temporal diária de um produto específico no período."""
    from app.domain.value_objects.codigo import Codigo
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | diario/produto periodo=%s..%s codigo=%s metrica=%s", data_inicio, data_fim, codigo, metrica.value)
    try:
        codigo_valido = Codigo(codigo).valor
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Código inválido: {codigo!r}")
    dominio = criar_dominio(source, data_inicio, data_fim)
    return RelatorioDiario(dominio.vendas).serie_por_produto(codigo_valido, metrica)


# ── Temporal (hora, dia-semana) ───────────────────────────────────────────────

@router.get("/temporal/hora", response_model=list[PontoHoraDTO])
@limiter.limit("20/minute")
def distribuicao_hora(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    metrica: Metrica = Query(Metrica.RECEITA),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna a distribuição de vendas por hora do dia no período informado."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | temporal/hora periodo=%s..%s metrica=%s", data_inicio, data_fim, metrica.value)
    dominio = criar_dominio(source, data_inicio, data_fim)
    return RelatorioTemporal(dominio.vendas).por_hora(metrica)


@router.get("/temporal/dia-semana", response_model=list[PontoDiaSemanaDTO])
@limiter.limit("20/minute")
def distribuicao_dia_semana(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    metrica: Metrica = Query(Metrica.RECEITA),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna a distribuição de vendas por dia da semana no período informado."""
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | temporal/dia-semana periodo=%s..%s metrica=%s", data_inicio, data_fim, metrica.value)
    dominio = criar_dominio(source, data_inicio, data_fim)
    return RelatorioTemporal(dominio.vendas).por_dia_semana(metrica)


# ── SKU ───────────────────────────────────────────────────────────────────────

@router.get("/sku", response_model=SkuDTO)
@limiter.limit("20/minute")
def sku(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    codigo: str = Query(...),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    """Retorna o resumo completo de um SKU (produto) no período informado."""
    from app.domain.value_objects.codigo import Codigo
    data_inicio, data_fim = _periodo(data_inicio, data_fim)
    logger.info("BI Request | sku periodo=%s..%s codigo=%s", data_inicio, data_fim, codigo)
    try:
        codigo_valido = Codigo(codigo).valor
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Código inválido: {codigo!r}")
    dominio = criar_dominio(source, data_inicio, data_fim)
    resultado = RelatorioSku(dominio.vendas, codigo_valido).resumo()
    if resultado is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado no período informado")
    return resultado


# ── Exportação Excel ──────────────────────────────────────────────────────────

@router.get("/exportar/excel")
@limiter.limit("10/minute")
def exportar_excel(
    request: Request,
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    relatorio: str = Query(...),
    dimensao: Dimensao = Query(Dimensao.PRODUTO),
    metrica: Metrica = Query(Metrica.RECEITA),
    top: int = Query(default=10, ge=1, le=100),
    codigo: str = Query(default=None),
    source: TransactionSource = Depends(get_transaction_source),
    _usuario: Usuario = Depends(require_supervisor),
):
    from app.application.bi.reporting.exportador import ExportadorExcel
    from app.domain.value_objects.codigo import Codigo

    data_inicio, data_fim = _periodo(data_inicio, data_fim)

    opcoes_validas = {
        "kpis", "receita", "quantidade",
        "curva-abc", "ranking", "trocas",
        "perdas", "consumo", "diario", "sku"
    }
    if relatorio not in opcoes_validas:
        raise HTTPException(
            status_code=400,
            detail=f"Relatório inválido. Opções: {sorted(opcoes_validas)}"
        )

    logger.info("BI Request | exportar/excel relatorio=%s periodo=%s..%s", relatorio, data_inicio, data_fim)
    from app.core.timer import temporizador

    with temporizador(f"BI Export {relatorio}", logger):
        dominio = criar_dominio(source, data_inicio, data_fim)
    rel = Relatorio(dominio.vendas, dominio.trocas)
    exportador = ExportadorExcel()
    dados: dict = {}

    if relatorio == "kpis":
        dados["KPIs"] = [rel.kpis().model_dump()]
    elif relatorio == "receita":
        dados["Receita"] = [i.model_dump() for i in rel.por_dimensao(dimensao, Metrica.RECEITA)]
    elif relatorio == "quantidade":
        dados["Quantidade"] = [i.model_dump() for i in rel.por_dimensao(dimensao, Metrica.QUANTIDADE)]
    elif relatorio == "curva-abc":
        dados["Curva ABC"] = [i.model_dump() for i in rel.curva_abc(dimensao)]
    elif relatorio == "ranking":
        dados["Ranking"] = [i.model_dump() for i in rel.ranking(metrica, top)]
    elif relatorio == "trocas":
        trocas_dto = rel.trocas_resumo()
        dados["Trocas Resumo"] = [{"total_trocas": trocas_dto.total_trocas, "taxa_troca_pct": trocas_dto.taxa_troca_pct}]
        dados["Trocas por Produto"] = [i.model_dump() for i in trocas_dto.por_produto]
    elif relatorio == "perdas":
        items = source.get_items(data_inicio, data_fim)
        perdas_dto = RelatorioMovimento(Perdas(items)).resumo()
        dados["Perdas Resumo"] = [{"total": perdas_dto.total}]
        dados["Perdas por Produto"] = [i.model_dump() for i in perdas_dto.por_produto]
    elif relatorio == "consumo":
        items = source.get_items(data_inicio, data_fim)
        consumo_dto = RelatorioMovimento(Consumo(items)).resumo()
        dados["Consumo Resumo"] = [{"total": consumo_dto.total}]
        dados["Consumo por Produto"] = [i.model_dump() for i in consumo_dto.por_produto]
    elif relatorio == "diario":
        dados["Série Diária"] = [i.model_dump() for i in RelatorioDiario(dominio.vendas).serie_temporal(metrica)]
    elif relatorio == "sku":
        if not codigo:
            raise HTTPException(status_code=400, detail="Parâmetro 'codigo' obrigatório para relatório SKU")
        try:
            codigo_valido = Codigo(codigo).valor
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"Código inválido: {codigo!r}")
        resultado = RelatorioSku(dominio.vendas, codigo_valido).resumo()
        if resultado is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado no período informado")
        dados["SKU"] = [resultado.model_dump(exclude={"ranking_dias", "distribuicao_hora"})]
        dados["Ranking Dias"] = [i.model_dump() for i in resultado.ranking_dias]
        dados["Distribuição Hora"] = [i.model_dump() for i in resultado.distribuicao_hora]

    conteudo = exportador.exportar(dados)
    nome_arquivo = f"bi_{relatorio}_{data_inicio}_{data_fim}.xlsx"

    return StreamingResponse(
        BytesIO(conteudo),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"},
    )
