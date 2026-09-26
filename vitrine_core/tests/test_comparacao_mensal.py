from datetime import date
from decimal import Decimal as D

import pytest

from vitrine_core.bi.equipe import (
    calcular_equipe,
    comparar_com_loja,
    meses_ate,
    periodo_anterior,
    serie_mensal_da_equipe,
    serie_mensal_do_vendedor,
)
from vitrine_core.datasets.tipos import VendaVendedorPeriodo


@pytest.mark.parametrize("inicio, fim, esperado", [
    (date(2026, 9, 1), date(2026, 9, 30), (date(2026, 8, 1), date(2026, 8, 31))),
    (date(2026, 3, 1), date(2026, 3, 31), (date(2026, 2, 1), date(2026, 2, 28))),
    (date(2026, 1, 1), date(2026, 1, 31), (date(2025, 12, 1), date(2025, 12, 31))),
    (date(2026, 7, 1), date(2026, 9, 30), (date(2026, 4, 1), date(2026, 6, 30))),
    (date(2026, 9, 1), date(2026, 9, 15), (date(2026, 8, 1), date(2026, 8, 15))),
    (date(2026, 3, 1), date(2026, 3, 31), (date(2026, 2, 1), date(2026, 2, 28))),
    (date(2026, 3, 1), date(2026, 3, 30), (date(2026, 2, 1), date(2026, 2, 28))),
    (date(2026, 9, 10), date(2026, 9, 16), (date(2026, 9, 3), date(2026, 9, 9))),
    (date(2026, 7, 1), date(2026, 9, 15), (date(2026, 4, 15), date(2026, 6, 30))),
])
def test_periodo_anterior_por_calendario(inicio, fim, esperado):
    assert periodo_anterior(inicio, fim) == esperado


def _linha(vendedor, bruto, atendimentos=10, pecas="20", trocas="0"):
    return VendaVendedorPeriodo(
        inicio=date(2026, 9, 1), fim=date(2026, 9, 30), vendedor=vendedor, atendimentos=atendimentos,
        pecas=D(pecas), faturamento_bruto=D(bruto), trocas=D(trocas),
    )


def _por_nome(resultado):
    return {v.vendedor: v for v in resultado.vendedores}


INI, FIM = date(2026, 9, 1), date(2026, 9, 30)


def test_novo_e_saidas_e_entradas_contra_o_mes_anterior():
    resultado = calcular_equipe(
        [_linha("Ana", "1000"), _linha("Bia", "500"), _linha(None, "50")],
        INI, FIM,
        anteriores=[_linha("Ana", "900"), _linha("Caio", "800")],
    )

    assert _por_nome(resultado)["Bia"].novo is True
    assert _por_nome(resultado)["Ana"].novo is False
    assert _por_nome(resultado)["Sem vendedor"].novo is False
    assert resultado.equipe.entradas == ["Bia"]
    assert resultado.equipe.saidas == ["Caio"]
    assert (resultado.equipe.vendedores_ativos, resultado.equipe.vendedores_ativos_anterior) == (2, 2)


def test_sem_periodo_anterior_ninguem_e_novo():
    resultado = calcular_equipe([_linha("Ana", "1000")], INI, FIM)

    assert _por_nome(resultado)["Ana"].novo is False
    assert resultado.equipe.entradas == [] and resultado.equipe.vendedores_ativos_anterior is None


def test_concentracao_dos_tres_maiores_so_com_mais_de_tres():
    poucos = calcular_equipe([_linha(n, "100") for n in "ABC"], INI, FIM)
    muitos = calcular_equipe([_linha("A", "600"), _linha("B", "200"), _linha("C", "100"), _linha("D", "60"), _linha("E", "40")], INI, FIM)

    assert poucos.equipe.concentracao_top3 is None
    assert muitos.equipe.concentracao_top3 == 0.9


def test_meses_ate_marca_o_corrente_como_parcial():
    meses = meses_ate(date(2026, 9, 26), 3)

    assert meses == [
        (date(2026, 7, 1), date(2026, 7, 31), False),
        (date(2026, 8, 1), date(2026, 8, 31), False),
        (date(2026, 9, 1), date(2026, 9, 26), True),
    ]
    assert meses_ate(date(2026, 9, 30), 1) == [(date(2026, 9, 1), date(2026, 9, 30), False)]


def test_serie_mensal_da_equipe_e_do_vendedor_com_lacunas():
    ago = [_linha("Ana", "1000", 10, "20", "50"), _linha("Bia", "500", 5, "5")]
    set_ = [_linha("Ana", "1200", 12, "30")]
    meses = [
        (date(2026, 7, 1), date(2026, 7, 31), False, []),
        (date(2026, 8, 1), date(2026, 8, 31), False, ago),
        (date(2026, 9, 1), date(2026, 9, 26), True, set_),
    ]

    equipe = serie_mensal_da_equipe(meses)
    bia = serie_mensal_do_vendedor(meses, "Bia")

    assert [p.sem_dados for p in equipe] == [True, False, False]
    assert (equipe[1].faturamento_liquido, equipe[1].vendedores_ativos) == (1450.0, 2)
    assert equipe[2].parcial is True
    assert [(p.sem_dados, p.ausente) for p in bia] == [(True, False), (False, False), (False, True)]
    assert bia[1].ticket_medio == 100.0
    assert serie_mensal_do_vendedor(meses, "ana")[1].taxa_troca == 0.05


def test_comparacao_com_a_loja_em_relativo():
    resultado = calcular_equipe([_linha("Ana", "3000", 10, "30", "300"), _linha("Bia", "1000", 10, "10")], INI, FIM)

    comparacao = comparar_com_loja(_por_nome(resultado)["Ana"], resultado.loja)

    assert comparacao.ticket_medio == 0.5
    assert comparacao.pa == 0.5
    assert comparacao.taxa_troca == round(0.1 / 0.075 - 1, 4)


def test_comparacao_com_mes_completo_so_compara_taxas_nao_totais():
    resultado = calcular_equipe(
        [_linha("Ana", "1200", 10, "20")], INI, date(2026, 9, 26),
        anteriores=[_linha("Ana", "3000", 30, "30")],
        anterior_exato=False,
        periodo_anterior_efetivo=(date(2026, 8, 1), date(2026, 8, 31)),
    )

    ana = _por_nome(resultado)["Ana"]
    assert resultado.comparacao_parcial is True
    assert (resultado.periodo_anterior.inicio, resultado.periodo_anterior.fim) == (date(2026, 8, 1), date(2026, 8, 31))
    assert ana.variacao_liquido is None
    assert ana.variacao_ticket_medio == 0.2
    assert ana.variacao_pa == 1.0
