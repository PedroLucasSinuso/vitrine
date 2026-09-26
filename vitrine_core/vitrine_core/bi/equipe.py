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
    novo: bool = False
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


class ResumoEquipe(BaseModel):
    vendedores_ativos: int
    vendedores_ativos_anterior: int | None = None
    entradas: list[str] = []
    saidas: list[str] = []
    concentracao_top3: float | None = None


class ResultadoEquipe(BaseModel):
    periodo: Periodo
    periodo_anterior: Periodo | None
    comparacao_parcial: bool = False
    competencia: str | None = None
    loja: IndicadoresLoja
    vendedores: list[IndicadoresVendedor]
    indisponivel: list[Indisponivel]
    equipe: ResumoEquipe | None = None


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


def _ultimo_dia_do_mes(dia: date) -> int:
    return calendar.monthrange(dia.year, dia.month)[1]


def _primeiro_do_mes_anterior(dia: date, meses: int = 1) -> date:
    indice = dia.year * 12 + dia.month - 1 - meses
    return date(indice // 12, indice % 12 + 1, 1)


def periodo_anterior(inicio: date, fim: date) -> tuple[date, date]:
    if inicio.day == 1:
        meses = (fim.year - inicio.year) * 12 + fim.month - inicio.month + 1
        if fim.day == _ultimo_dia_do_mes(fim):
            return _primeiro_do_mes_anterior(inicio, meses), inicio - timedelta(days=1)
        if meses == 1:
            comeco = _primeiro_do_mes_anterior(inicio)
            return comeco, comeco.replace(day=min(fim.day, _ultimo_dia_do_mes(comeco)))
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


def _ativos(consolidado: dict[str | None, dict]) -> set[str]:
    return {nome for nome, v in consolidado.items() if nome is not None and v["bruto"] > 0}


def _resumo_da_equipe(atual: dict[str | None, dict], anterior: dict[str | None, dict]) -> ResumoEquipe:
    ativos = _ativos(atual)
    ativos_anterior = _ativos(anterior) if anterior else None
    nomeados = sorted((atual[n]["bruto"] for n in ativos), reverse=True)
    total = sum(nomeados, ZERO)
    concentracao = round(float(sum(nomeados[:3], ZERO) / total), 4) if len(nomeados) > 3 and total else None
    return ResumoEquipe(
        vendedores_ativos=len(ativos),
        vendedores_ativos_anterior=len(ativos_anterior) if ativos_anterior is not None else None,
        entradas=sorted(ativos - ativos_anterior, key=str.upper) if ativos_anterior is not None else [],
        saidas=sorted(ativos_anterior - ativos, key=str.upper) if ativos_anterior is not None else [],
        concentracao_top3=concentracao,
    )


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
    anterior_exato: bool = True,
    periodo_anterior_efetivo: tuple[date, date] | None = None,
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
            variacao_liquido=_variacao(v["liquido"], ant["liquido"] if ant else None) if anterior_exato else None,
            variacao_ticket_medio=_variacao(ticket, _razao(ant["bruto"], ant["atendimentos"]) if ant else None),
            variacao_pa=_variacao(pa, _razao(ant["pecas"], ant["atendimentos"]) if ant else None),
            novo=bool(anterior) and chave is not None and ant is None,
            **_indicadores_de_meta(v["liquido"], meta, fator),
            **_indicadores_de_contato(v["atendimentos"], contatos_por_vendedor.get(chave.upper()) if chave else None),
        ))
    vendedores.sort(key=lambda i: (i.sem_vendedor, -i.faturamento_liquido))

    periodo_ant = None
    if anteriores:
        ini_ant, fim_ant = periodo_anterior_efetivo or periodo_anterior(inicio, fim)
        periodo_ant = Periodo(inicio=ini_ant, fim=fim_ant)

    meta_loja = sum((m.valor for m in metas.values()), ZERO) if metas else None
    indicadores_meta_loja = _indicadores_de_meta(liquido_loja, Meta(meta_loja) if meta_loja else None, fator)
    indicadores_meta_loja.pop("comissao_estimada")

    resumo = _resumo_da_equipe(atual, anterior)

    return ResultadoEquipe(
        periodo=Periodo(inicio=inicio, fim=fim),
        periodo_anterior=periodo_ant,
        comparacao_parcial=bool(anteriores) and not anterior_exato,
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
        equipe=resumo,
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


class PontoMensal(BaseModel):
    competencia: str
    inicio: date
    fim: date
    parcial: bool
    sem_dados: bool
    ausente: bool
    faturamento_liquido: float | None = None
    atendimentos: int | None = None
    ticket_medio: float | None = None
    pa: float | None = None
    taxa_troca: float | None = None
    vendedores_ativos: int | None = None


def meses_ate(fim: date, quantidade: int) -> list[tuple[date, date, bool]]:
    meses = []
    for atras in range(quantidade - 1, -1, -1):
        inicio = _primeiro_do_mes_anterior(fim.replace(day=1), atras) if atras else fim.replace(day=1)
        ultimo = inicio.replace(day=_ultimo_dia_do_mes(inicio))
        parcial = atras == 0 and fim < ultimo
        meses.append((inicio, fim if atras == 0 and parcial else ultimo, parcial))
    return meses


def _ponto_mensal(inicio: date, fim: date, parcial: bool, linhas: list[VendaVendedorPeriodo], vendedor: str | None, equipe: bool) -> PontoMensal:
    base = dict(competencia=f"{inicio.year:04d}-{inicio.month:02d}", inicio=inicio, fim=fim, parcial=parcial)
    if not linhas:
        return PontoMensal(**base, sem_dados=True, ausente=False)
    consolidado = _consolidar(linhas)
    if equipe:
        escolhidos = list(consolidado.values())
    else:
        alvo = _chave(vendedor)
        escolhido = next((v for n, v in consolidado.items() if (n or "").upper() == (alvo or "").upper() and (n is None) == (alvo is None)), None)
        if escolhido is None:
            return PontoMensal(**base, sem_dados=False, ausente=True)
        escolhidos = [escolhido]
    bruto = sum((v["bruto"] for v in escolhidos), ZERO)
    trocas = sum((v["trocas"] for v in escolhidos), ZERO)
    liquido = sum((v["liquido"] for v in escolhidos), ZERO)
    atendimentos = sum(v["atendimentos"] for v in escolhidos)
    pecas = sum((v["pecas"] for v in escolhidos), ZERO)
    return PontoMensal(
        **base,
        sem_dados=False,
        ausente=False,
        faturamento_liquido=round(float(liquido), 2),
        atendimentos=atendimentos,
        ticket_medio=round(float(_razao(bruto, atendimentos)), 2),
        pa=round(float(_razao(pecas, atendimentos)), 2),
        taxa_troca=round(float(_razao(trocas, bruto)), 4),
        vendedores_ativos=len(_ativos(consolidado)) if equipe else None,
    )


def serie_mensal_da_equipe(meses: list[tuple[date, date, bool, list[VendaVendedorPeriodo]]]) -> list[PontoMensal]:
    return [_ponto_mensal(i, f, p, linhas, None, equipe=True) for i, f, p, linhas in meses]


def serie_mensal_do_vendedor(meses: list[tuple[date, date, bool, list[VendaVendedorPeriodo]]], vendedor: str | None) -> list[PontoMensal]:
    return [_ponto_mensal(i, f, p, linhas, vendedor, equipe=False) for i, f, p, linhas in meses]


class ComparacaoComLoja(BaseModel):
    ticket_medio: float | None = None
    pa: float | None = None
    preco_medio_peca: float | None = None
    taxa_troca: float | None = None


def _relativo(valor: float, referencia: float) -> float | None:
    return round(valor / referencia - 1, 4) if referencia else None


def comparar_com_loja(vendedor: IndicadoresVendedor, loja: IndicadoresLoja) -> ComparacaoComLoja:
    preco_medio_loja = loja.faturamento_bruto / (loja.pa * loja.atendimentos) if loja.pa and loja.atendimentos else 0.0
    taxa_troca_loja = loja.trocas / loja.faturamento_bruto if loja.faturamento_bruto else 0.0
    taxa_troca_vendedor = vendedor.trocas / vendedor.faturamento_bruto if vendedor.faturamento_bruto else 0.0
    return ComparacaoComLoja(
        ticket_medio=_relativo(vendedor.ticket_medio, loja.ticket_medio),
        pa=_relativo(vendedor.pa, loja.pa),
        preco_medio_peca=_relativo(vendedor.preco_medio_peca, preco_medio_loja),
        taxa_troca=_relativo(taxa_troca_vendedor, taxa_troca_loja),
    )


class DetalheVendedor(BaseModel):
    periodo: Periodo
    periodo_anterior: Periodo | None
    comparacao_parcial: bool = False
    indicadores: IndicadoresVendedor
    loja: IndicadoresLoja
    comparacao_loja: ComparacaoComLoja
    posicao: int | None = None
    total_vendedores: int
    serie_mensal: list[PontoMensal] | None = None
    serie_diaria: list[PontoSerieVendedor] | None = None
    mix: list[ItemMixVendedor] | None = None
    indisponivel: list[Indisponivel] = []
