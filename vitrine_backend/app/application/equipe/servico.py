from datetime import date

from vitrine_core.bi.equipe import (
    REQUISITOS,
    Meta,
    aplicar_aliases,
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
    return calcular_equipe(
        aplicar_aliases(fonte.vendedor_periodo(inicio, fim), aliases),
        inicio,
        fim,
        anteriores=aplicar_aliases(fonte.vendedor_periodo(inicio_ant, fim_ant), aliases) or None,
        atendimentos_loja=fonte.atendimentos_loja(inicio, fim),
        tipos_disponiveis=fonte.tipos,
        metas=metas,
        contatos=aplicar_aliases(fonte.contatos(inicio, fim) or [], aliases),
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
