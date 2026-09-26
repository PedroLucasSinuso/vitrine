from datetime import date
from decimal import Decimal as D

from vitrine_core.bi.equipe import Meta, aplicar_aliases, calcular_equipe, competencia_do_periodo
from vitrine_core.datasets.tipos import VendaVendedorPeriodo

SET_INI, SET_FIM = date(2026, 9, 1), date(2026, 9, 30)


def _linha(vendedor, liquido):
    return VendaVendedorPeriodo(
        inicio=SET_INI, fim=SET_FIM, vendedor=vendedor, atendimentos=10, pecas=D("10"),
        faturamento_bruto=D(liquido), faturamento_liquido=D(liquido),
    )


def _por_nome(resultado):
    return {v.vendedor: v for v in resultado.vendedores}


def test_atingimento_comissao_e_projecao_no_mes_corrente():
    resultado = calcular_equipe(
        [_linha("Ana", "6000"), _linha("Bruno", "3000")],
        SET_INI, SET_FIM,
        metas={"ana": Meta(D("10000"), D("2")), "Bruno": Meta(D("5000"), D("1.5"))},
        hoje=date(2026, 9, 15),
    )

    ana = _por_nome(resultado)["Ana"]
    assert resultado.competencia == "2026-09"
    assert ana.meta == 10000.0
    assert ana.atingimento == 0.6
    assert ana.comissao_estimada == 120.0
    assert ana.projecao == 12000.0
    assert resultado.loja.meta == 15000.0
    assert resultado.loja.atingimento == 0.6
    assert resultado.loja.projecao == 18000.0


def test_mes_encerrado_nao_tem_projecao():
    resultado = calcular_equipe([_linha("Ana", "6000")], SET_INI, SET_FIM,
                                metas={"Ana": Meta(D("10000"))}, hoje=date(2026, 10, 5))

    assert _por_nome(resultado)["Ana"].projecao is None
    assert _por_nome(resultado)["Ana"].atingimento == 0.6


def test_periodo_que_atravessa_meses_nao_usa_metas():
    resultado = calcular_equipe([_linha("Ana", "6000")], date(2026, 8, 20), SET_FIM,
                                metas={"Ana": Meta(D("10000"))})

    assert resultado.competencia is None
    assert _por_nome(resultado)["Ana"].meta is None
    assert resultado.loja.meta is None


def test_vendedor_sem_meta_fica_sem_indicadores_de_meta():
    resultado = calcular_equipe([_linha("Ana", "6000"), _linha(None, "100")], SET_INI, SET_FIM,
                                metas={"Ana": Meta(D("10000"))}, hoje=date(2026, 9, 10))

    assert _por_nome(resultado)["Sem vendedor"].meta is None


def test_competencia_do_periodo():
    assert competencia_do_periodo(date(2026, 2, 1), date(2026, 2, 28)) == "2026-02"
    assert competencia_do_periodo(date(2026, 2, 10), date(2026, 3, 2)) is None


def test_aliases_juntam_nomes_escritos_de_jeitos_diferentes():
    linhas = aplicar_aliases(
        [_linha("MARIANA S.", "100"), _linha("Mariana Souza", "50"), _linha("Bruno", "10")],
        {"mariana s.": "Mariana Souza"},
    )

    resultado = calcular_equipe(linhas, SET_INI, SET_FIM)

    assert _por_nome(resultado)["Mariana Souza"].faturamento_liquido == 150.0
    assert "MARIANA S." not in _por_nome(resultado)


def test_serie_soma_o_mesmo_dia_quando_dois_nomes_viram_um():
    from vitrine_core.bi.equipe import serie_do_vendedor
    from vitrine_core.datasets.tipos import VendaDiaria

    diarias = aplicar_aliases([
        VendaDiaria(data=SET_INI, vendedor="MARIANA S.", faturamento_bruto=D("100"), atendimentos=2, pecas=D("4")),
        VendaDiaria(data=SET_INI, vendedor="Mariana Souza", faturamento_bruto=D("50"), atendimentos=1, pecas=D("2")),
    ], {"MARIANA S.": "Mariana Souza"})

    serie = serie_do_vendedor(diarias, "Mariana Souza")

    assert [(p.faturamento_bruto, p.atendimentos, p.pa) for p in serie] == [(150.0, 3, 2.0)]
