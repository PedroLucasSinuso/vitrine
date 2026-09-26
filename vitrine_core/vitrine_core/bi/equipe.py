from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from pydantic import BaseModel

from vitrine_core.datasets.capacidades import tipos_derivaveis
from vitrine_core.datasets.tipos import ItemVenda, Operacao, TipoDataset, VendaDiaria, VendaVendedorPeriodo

SEM_VENDEDOR = "Sem vendedor"
ZERO = Decimal("0")

REQUISITOS: dict[str, tuple[TipoDataset, str]] = {
    "serie_diaria": (TipoDataset.VENDAS_DIARIAS, "Os dados enviados não trazem vendas por dia."),
    "mix_categoria": (TipoDataset.ITENS_VENDA, "Os dados enviados não trazem os itens vendidos."),
    "conversao_contatos": (TipoDataset.CONTATOS_VENDEDOR, "Nenhum relatório de contatos foi enviado."),
}


class Periodo(BaseModel):
    inicio: date
    fim: date


class Indisponivel(BaseModel):
    indicador: str
    motivo: str


class IndicadoresVendedor(BaseModel):
    vendedor: str
    sem_vendedor: bool
    faturamento_bruto: float
    trocas: float
    faturamento_liquido: float
    atendimentos: int
    pecas: float
    ticket_medio: float
    pa: float
    preco_medio_peca: float
    participacao: float
    variacao_liquido: float | None = None
    variacao_ticket_medio: float | None = None
    variacao_pa: float | None = None


class IndicadoresLoja(BaseModel):
    faturamento_bruto: float
    trocas: float
    faturamento_liquido: float
    atendimentos: int
    atendimentos_somados_por_vendedor: bool
    ticket_medio: float
    pa: float


class ResultadoEquipe(BaseModel):
    periodo: Periodo
    periodo_anterior: Periodo | None
    loja: IndicadoresLoja
    vendedores: list[IndicadoresVendedor]
    indisponivel: list[Indisponivel]


def periodo_anterior(inicio: date, fim: date) -> tuple[date, date]:
    duracao = fim - inicio
    fim_anterior = inicio - timedelta(days=1)
    return fim_anterior - duracao, fim_anterior


def _razao(numerador: Decimal, denominador: Decimal | int) -> Decimal:
    return numerador / Decimal(denominador) if denominador else ZERO


def _variacao(atual: Decimal, anterior: Decimal | None) -> float | None:
    if anterior is None or anterior == 0:
        return None
    return round(float((atual - anterior) / anterior), 4)


def _consolidar(linhas: list[VendaVendedorPeriodo]) -> dict[str | None, dict]:
    acumulado: dict[str | None, dict] = defaultdict(
        lambda: {"bruto": ZERO, "trocas": ZERO, "liquido": ZERO, "atendimentos": 0, "pecas": ZERO}
    )
    for linha in linhas:
        chave = (linha.vendedor or "").strip() or None
        valores = acumulado[chave]
        liquido = (
            linha.faturamento_liquido
            if linha.faturamento_liquido is not None
            else linha.faturamento_bruto - linha.trocas
        )
        valores["bruto"] += linha.faturamento_bruto
        valores["trocas"] += linha.trocas
        valores["liquido"] += liquido
        valores["atendimentos"] += linha.atendimentos
        valores["pecas"] += linha.pecas
    return acumulado


def _indisponiveis(tipos_disponiveis: set[TipoDataset] | None) -> list[Indisponivel]:
    if tipos_disponiveis is None:
        return []
    derivaveis = tipos_derivaveis(tipos_disponiveis)
    return [
        Indisponivel(indicador=indicador, motivo=motivo)
        for indicador, (tipo, motivo) in REQUISITOS.items()
        if tipo not in derivaveis
    ]


def calcular_equipe(
    linhas: list[VendaVendedorPeriodo],
    inicio: date,
    fim: date,
    anteriores: list[VendaVendedorPeriodo] | None = None,
    atendimentos_loja: int | None = None,
    tipos_disponiveis: set[TipoDataset] | None = None,
) -> ResultadoEquipe:
    atual = _consolidar(linhas)
    anterior = _consolidar(anteriores) if anteriores else {}

    bruto_loja = sum((v["bruto"] for v in atual.values()), ZERO)
    trocas_loja = sum((v["trocas"] for v in atual.values()), ZERO)
    liquido_loja = sum((v["liquido"] for v in atual.values()), ZERO)
    pecas_loja = sum((v["pecas"] for v in atual.values()), ZERO)
    somados = atendimentos_loja is None
    atendimentos = sum(v["atendimentos"] for v in atual.values()) if somados else atendimentos_loja

    vendedores = []
    for chave, v in atual.items():
        ticket = _razao(v["bruto"], v["atendimentos"])
        pa = _razao(v["pecas"], v["atendimentos"])
        ant = anterior.get(chave)
        vendedores.append(IndicadoresVendedor(
            vendedor=chave or SEM_VENDEDOR,
            sem_vendedor=chave is None,
            faturamento_bruto=round(float(v["bruto"]), 2),
            trocas=round(float(v["trocas"]), 2),
            faturamento_liquido=round(float(v["liquido"]), 2),
            atendimentos=v["atendimentos"],
            pecas=round(float(v["pecas"]), 3),
            ticket_medio=round(float(ticket), 2),
            pa=round(float(pa), 2),
            preco_medio_peca=round(float(_razao(v["bruto"], v["pecas"])), 2),
            participacao=round(float(_razao(v["bruto"], bruto_loja)), 4),
            variacao_liquido=_variacao(v["liquido"], ant["liquido"] if ant else None),
            variacao_ticket_medio=_variacao(ticket, _razao(ant["bruto"], ant["atendimentos"]) if ant else None),
            variacao_pa=_variacao(pa, _razao(ant["pecas"], ant["atendimentos"]) if ant else None),
        ))
    vendedores.sort(key=lambda i: (i.sem_vendedor, -i.faturamento_liquido))

    periodo_ant = None
    if anteriores:
        ini_ant, fim_ant = periodo_anterior(inicio, fim)
        periodo_ant = Periodo(inicio=ini_ant, fim=fim_ant)

    return ResultadoEquipe(
        periodo=Periodo(inicio=inicio, fim=fim),
        periodo_anterior=periodo_ant,
        loja=IndicadoresLoja(
            faturamento_bruto=round(float(bruto_loja), 2),
            trocas=round(float(trocas_loja), 2),
            faturamento_liquido=round(float(liquido_loja), 2),
            atendimentos=atendimentos,
            atendimentos_somados_por_vendedor=somados,
            ticket_medio=round(float(_razao(bruto_loja, atendimentos)), 2),
            pa=round(float(_razao(pecas_loja, atendimentos)), 2),
        ),
        vendedores=vendedores,
        indisponivel=_indisponiveis(tipos_disponiveis),
    )


class PontoSerieVendedor(BaseModel):
    data: date
    faturamento_bruto: float
    atendimentos: int
    pa: float


class ItemMixVendedor(BaseModel):
    grupo: str
    familia: str
    receita: float
    participacao: float


def _mesmo_vendedor(nome: str | None, vendedor: str | None) -> bool:
    return ((nome or "").strip() or None) == ((vendedor or "").strip() or None)


def serie_do_vendedor(diarias: list[VendaDiaria], vendedor: str | None) -> list[PontoSerieVendedor]:
    return [
        PontoSerieVendedor(
            data=d.data,
            faturamento_bruto=round(float(d.faturamento_bruto), 2),
            atendimentos=d.atendimentos,
            pa=round(float(_razao(d.pecas, d.atendimentos)), 2),
        )
        for d in sorted(diarias, key=lambda d: d.data)
        if _mesmo_vendedor(d.vendedor, vendedor)
    ]


def mix_do_vendedor(itens: list[ItemVenda], vendedor: str | None) -> list[ItemMixVendedor]:

    receita: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    for item in itens:
        if item.operacao == Operacao.VENDA and _mesmo_vendedor(item.vendedor, vendedor):
            receita[(item.grupo, item.familia)] += item.valor
    total = sum(receita.values(), ZERO)
    mix = [
        ItemMixVendedor(
            grupo=grupo, familia=familia,
            receita=round(float(valor), 2),
            participacao=round(float(_razao(valor, total)), 4),
        )
        for (grupo, familia), valor in receita.items()
    ]
    return sorted(mix, key=lambda m: -m.receita)
