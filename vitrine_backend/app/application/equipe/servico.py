from datetime import date

from vitrine_core.bi.equipe import (
    REQUISITOS,
    ItemMixVendedor,
    PontoSerieVendedor,
    ResultadoEquipe,
    calcular_equipe,
    mix_do_vendedor,
    periodo_anterior,
    serie_do_vendedor,
)

from app.application.equipe.fonte import FonteEquipe


class IndicadorIndisponivel(Exception):
    def __init__(self, indicador: str):
        super().__init__(REQUISITOS[indicador][1])


def resultado_equipe(fonte: FonteEquipe, inicio: date, fim: date) -> ResultadoEquipe:
    inicio_ant, fim_ant = periodo_anterior(inicio, fim)
    return calcular_equipe(
        fonte.vendedor_periodo(inicio, fim),
        inicio,
        fim,
        anteriores=fonte.vendedor_periodo(inicio_ant, fim_ant) or None,
        atendimentos_loja=fonte.atendimentos_loja(inicio, fim),
        tipos_disponiveis=fonte.tipos,
    )


def serie(fonte: FonteEquipe, inicio: date, fim: date, vendedor: str | None) -> list[PontoSerieVendedor]:
    diarias = fonte.diarias(inicio, fim)
    if diarias is None:
        raise IndicadorIndisponivel("serie_diaria")
    return serie_do_vendedor(diarias, vendedor)


def mix(fonte: FonteEquipe, inicio: date, fim: date, vendedor: str | None) -> list[ItemMixVendedor]:
    itens = fonte.itens(inicio, fim)
    if itens is None:
        raise IndicadorIndisponivel("mix_categoria")
    return mix_do_vendedor(itens, vendedor)
