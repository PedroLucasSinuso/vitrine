import calendar
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal

from pydantic import BaseModel

from vitrine_core.datasets.capacidades import tipos_derivaveis
from vitrine_core.datasets.tipos import (
    ContatoVendedor,
    ItemVenda,
    Operacao,
    TipoDataset,
    VendaDiaria,
    VendaVendedorPeriodo,
)

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
    meta: float | None = None
    atingimento: float | None = None
    projecao: float | None = None
    comissao_estimada: float | None = None
    contatos: int | None = None
    conversao: float | None = None


class IndicadoresLoja(BaseModel):
    faturamento_bruto: float
    trocas: float
    faturamento_liquido: float
    atendimentos: int
    atendimentos_somados_por_vendedor: bool
    ticket_medio: float
    pa: float
    meta: float | None = None
    atingimento: float | None = None
    projecao: float | None = None


class ResultadoEquipe(BaseModel):
    periodo: Periodo
    periodo_anterior: Periodo | None
    competencia: str | None = None
    loja: IndicadoresLoja
    vendedores: list[IndicadoresVendedor]
    indisponivel: list[Indisponivel]


@dataclass(frozen=True)
class Meta:
    valor: Decimal
    percentual_comissao: Decimal = ZERO


def competencia_do_periodo(inicio: date, fim: date) -> str | None:
    if (inicio.year, inicio.month) != (fim.year, fim.month):
        return None
    return f"{inicio.year:04d}-{inicio.month:02d}"


def _fator_de_projecao(competencia: str, hoje: date) -> Decimal | None:
    ano, mes = map(int, competencia.split("-"))
    if (hoje.year, hoje.month) != (ano, mes):
        return None
    dias_no_mes = calendar.monthrange(ano, mes)[1]
    return Decimal(dias_no_mes) / Decimal(hoje.day)


def _chave(nome: str | None) -> str | None:
    return (nome or "").strip() or None


def aplicar_aliases(linhas: list, aliases: dict[str, str]) -> list:
    if not aliases:
        return linhas
    normalizados = {origem.strip().upper(): destino for origem, destino in aliases.items()}
    resultado = []
    for linha in linhas:
        nome = _chave(linha.vendedor)
        destino = normalizados.get(nome.upper()) if nome else None
        resultado.append(replace(linha, vendedor=destino) if destino else linha)
    return resultado


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


def _indicadores_de_meta(liquido: Decimal, meta: Meta | None, fator: Decimal | None) -> dict:
    if meta is None or not meta.valor:
        return {"meta": None, "atingimento": None, "projecao": None, "comissao_estimada": None}
    projecao = liquido * fator if fator is not None else None
    return {
        "meta": round(float(meta.valor), 2),
        "atingimento": round(float(liquido / meta.valor), 4),
        "projecao": round(float(projecao), 2) if projecao is not None else None,
        "comissao_estimada": round(float(liquido * meta.percentual_comissao / 100), 2),
    }


def _indicadores_de_contato(atendimentos: int, contatos: int | None) -> dict:
    if not contatos:
        return {"contatos": None, "conversao": None}
    return {"contatos": contatos, "conversao": round(atendimentos / contatos, 4)}


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
    metas: dict[str, Meta] | None = None,
    hoje: date | None = None,
    contatos: list[ContatoVendedor] | None = None,
) -> ResultadoEquipe:
    contatos_por_vendedor: dict[str, int] = defaultdict(int)
    for contato in contatos or []:
        chave_contato = _chave(contato.vendedor)
        if chave_contato:
            contatos_por_vendedor[chave_contato.upper()] += contato.contatos
    competencia = competencia_do_periodo(inicio, fim)
    metas = {k.strip().upper(): v for k, v in (metas or {}).items()} if competencia else {}
    fator = _fator_de_projecao(competencia, hoje or date.today()) if competencia else None
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
        meta = metas.get(chave.upper()) if chave else None
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
            **_indicadores_de_meta(v["liquido"], meta, fator),
            **_indicadores_de_contato(v["atendimentos"], contatos_por_vendedor.get(chave.upper()) if chave else None),
        ))
    vendedores.sort(key=lambda i: (i.sem_vendedor, -i.faturamento_liquido))

    periodo_ant = None
    if anteriores:
        ini_ant, fim_ant = periodo_anterior(inicio, fim)
        periodo_ant = Periodo(inicio=ini_ant, fim=fim_ant)

    meta_loja = sum((m.valor for m in metas.values()), ZERO) if metas else None
    indicadores_meta_loja = _indicadores_de_meta(liquido_loja, Meta(meta_loja) if meta_loja else None, fator)
    indicadores_meta_loja.pop("comissao_estimada")

    return ResultadoEquipe(
        periodo=Periodo(inicio=inicio, fim=fim),
        periodo_anterior=periodo_ant,
        competencia=competencia,
        loja=IndicadoresLoja(
            faturamento_bruto=round(float(bruto_loja), 2),
            trocas=round(float(trocas_loja), 2),
            faturamento_liquido=round(float(liquido_loja), 2),
            atendimentos=atendimentos,
            atendimentos_somados_por_vendedor=somados,
            ticket_medio=round(float(_razao(bruto_loja, atendimentos)), 2),
            pa=round(float(_razao(pecas_loja, atendimentos)), 2),
            **indicadores_meta_loja,
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
    por_dia: dict[date, dict] = defaultdict(lambda: {"bruto": ZERO, "atendimentos": 0, "pecas": ZERO})
    for d in diarias:
        if _mesmo_vendedor(d.vendedor, vendedor):
            dia = por_dia[d.data]
            dia["bruto"] += d.faturamento_bruto
            dia["atendimentos"] += d.atendimentos
            dia["pecas"] += d.pecas
    return [
        PontoSerieVendedor(
            data=dia,
            faturamento_bruto=round(float(v["bruto"]), 2),
            atendimentos=v["atendimentos"],
            pa=round(float(_razao(v["pecas"], v["atendimentos"])), 2),
        )
        for dia, v in sorted(por_dia.items())
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
