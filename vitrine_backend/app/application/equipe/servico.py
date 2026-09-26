from datetime import date

from vitrine_core.bi.equipe import (
    REQUISITOS,
    DetalheVendedor,
    Meta,
    PontoMensal,
    aplicar_aliases,
    comparar_com_loja,
    meses_ate,
    serie_mensal_da_equipe,
    serie_mensal_do_vendedor,
    ItemMixVendedor,
    PontoSerieVendedor,
    ResultadoEquipe,
    calcular_equipe,
    mix_do_vendedor,
    periodo_anterior,
    serie_do_vendedor,
)

from app.application.equipe.fonte import FonteEquipe
from vitrine_core.bi.grade import ResultadoGrade, calcular_grade


class IndicadorIndisponivel(Exception):
    def __init__(self, indicador: str):
        super().__init__(REQUISITOS[indicador][1])


def resultado_equipe(
    fonte: FonteEquipe,
    inicio: date,
    fim: date,
    metas: dict[str, Meta] | None = None,
    aliases: dict[str, str] | None = None,
) -> ResultadoEquipe:
    aliases = aliases or {}
    inicio_ant, fim_ant = periodo_anterior(inicio, fim)
    comparativo = fonte.comparativo(inicio_ant, fim_ant)
    return calcular_equipe(
        aplicar_aliases(fonte.vendedor_periodo(inicio, fim), aliases),
        inicio,
        fim,
        anteriores=aplicar_aliases(comparativo.linhas, aliases) or None,
        atendimentos_loja=fonte.atendimentos_loja(inicio, fim),
        tipos_disponiveis=fonte.tipos,
        metas=metas,
        contatos=aplicar_aliases(fonte.contatos(inicio, fim) or [], aliases),
        anterior_exato=comparativo.exato,
        periodo_anterior_efetivo=(comparativo.inicio, comparativo.fim),
    )


def serie(
    fonte: FonteEquipe, inicio: date, fim: date, vendedor: str | None, aliases: dict[str, str] | None = None
) -> list[PontoSerieVendedor]:
    diarias = fonte.diarias(inicio, fim)
    if diarias is None:
        raise IndicadorIndisponivel("serie_diaria")
    return serie_do_vendedor(aplicar_aliases(diarias, aliases or {}), vendedor)


def mix(
    fonte: FonteEquipe, inicio: date, fim: date, vendedor: str | None, aliases: dict[str, str] | None = None
) -> list[ItemMixVendedor]:
    itens = fonte.itens(inicio, fim)
    if itens is None:
        raise IndicadorIndisponivel("mix_categoria")
    return mix_do_vendedor(aplicar_aliases(itens, aliases or {}), vendedor)


def grade(fonte: FonteEquipe, inicio: date, fim: date, grupo: str | None, familia: str | None) -> ResultadoGrade:
    itens = fonte.itens(inicio, fim)
    if itens is None:
        raise IndicadorIndisponivel("mix_categoria")
    return calcular_grade(itens, grupo, familia)


class VendedorNaoEncontrado(Exception):
    pass


MESES_PADRAO = 6
MESES_MAXIMO = 12
MESES_MINIMO_PARA_EVOLUCAO = 2


def _meses_com_dados(fonte: FonteEquipe, fim: date, quantidade: int, aliases: dict[str, str]):
    return [
        (inicio, ultimo, parcial, aplicar_aliases(fonte.vendedor_periodo(inicio, ultimo), aliases))
        for inicio, ultimo, parcial in meses_ate(fim, quantidade)
    ]


def serie_mensal_equipe(fonte: FonteEquipe, fim: date, quantidade: int, aliases: dict[str, str]) -> list[PontoMensal]:
    return serie_mensal_da_equipe(_meses_com_dados(fonte, fim, quantidade, aliases))


def serie_mensal_vendedor(
    fonte: FonteEquipe, fim: date, quantidade: int, vendedor: str | None, aliases: dict[str, str]
) -> list[PontoMensal]:
    return serie_mensal_do_vendedor(_meses_com_dados(fonte, fim, quantidade, aliases), vendedor)


def _opcional(chamada):
    try:
        return chamada()
    except IndicadorIndisponivel:
        return None


def detalhe_do_vendedor(
    fonte: FonteEquipe,
    inicio: date,
    fim: date,
    nome: str,
    metas: dict[str, Meta] | None = None,
    aliases: dict[str, str] | None = None,
) -> DetalheVendedor:
    aliases = aliases or {}
    resultado = resultado_equipe(fonte, inicio, fim, metas=metas, aliases=aliases)
    nomeados = [v for v in resultado.vendedores if not v.sem_vendedor]
    escolhido = next((v for v in nomeados if v.vendedor.upper() == nome.strip().upper()), None)
    if escolhido is None:
        raise VendedorNaoEncontrado(nome)

    evolucao = serie_mensal_vendedor(fonte, fim, MESES_PADRAO, escolhido.vendedor, aliases)
    com_dados = [p for p in evolucao if not p.sem_dados and not p.ausente]
    return DetalheVendedor(
        periodo=resultado.periodo,
        periodo_anterior=resultado.periodo_anterior,
        comparacao_parcial=resultado.comparacao_parcial,
        indicadores=escolhido,
        loja=resultado.loja,
        comparacao_loja=comparar_com_loja(escolhido, resultado.loja),
        posicao=nomeados.index(escolhido) + 1,
        total_vendedores=len(nomeados),
        serie_mensal=evolucao if len(com_dados) >= MESES_MINIMO_PARA_EVOLUCAO else None,
        serie_diaria=_opcional(lambda: serie(fonte, inicio, fim, escolhido.vendedor, aliases)),
        mix=_opcional(lambda: mix(fonte, inicio, fim, escolhido.vendedor, aliases)),
        indisponivel=[i for i in resultado.indisponivel if i.indicador != "conversao_contatos"],
    )
