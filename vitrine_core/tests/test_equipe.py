from datetime import date
from decimal import Decimal as D

import pytest

from vitrine_core.bi.equipe import SEM_VENDEDOR, calcular_equipe, periodo_anterior
from vitrine_core.datasets.agregacao import atendimentos_da_loja, vendedor_periodo
from vitrine_core.datasets.tipos import ItemVenda, Operacao, TipoDataset, VendaVendedorPeriodo

INI, FIM = date(2026, 9, 1), date(2026, 9, 30)


def _linha(vendedor, bruto, atendimentos, pecas, trocas="0", liquido=None):
    return VendaVendedorPeriodo(
        inicio=INI, fim=FIM, vendedor=vendedor, atendimentos=atendimentos, pecas=D(pecas),
        faturamento_bruto=D(bruto), trocas=D(trocas),
        faturamento_liquido=D(liquido) if liquido is not None else None,
    )


def _por_nome(resultado):
    return {v.vendedor: v for v in resultado.vendedores}


def test_indicadores_por_vendedor_calculados_a_mao():
    resultado = calcular_equipe([
        _linha("Ana", "3000", 20, "50", trocas="200"),
        _linha("Bruno", "1000", 25, "30"),
    ], INI, FIM)

    ana = _por_nome(resultado)["Ana"]
    assert ana.faturamento_liquido == 2800.0
    assert ana.ticket_medio == 150.0
    assert ana.pa == 2.5
    assert ana.preco_medio_peca == 60.0
    assert ana.participacao == 0.75


def test_liquido_informado_pelo_relatorio_tem_prioridade():
    resultado = calcular_equipe([_linha("Ana", "1000", 10, "10", trocas="100", liquido="950")], INI, FIM)

    assert _por_nome(resultado)["Ana"].faturamento_liquido == 950.0


def test_ordena_por_liquido_e_deixa_sem_vendedor_por_ultimo():
    resultado = calcular_equipe([
        _linha(None, "9000", 5, "5"),
        _linha("Bruno", "1000", 10, "10"),
        _linha("Ana", "2000", 10, "10"),
    ], INI, FIM)

    assert [v.vendedor for v in resultado.vendedores] == ["Ana", "Bruno", SEM_VENDEDOR]
    assert resultado.vendedores[-1].sem_vendedor


def test_linhas_do_mesmo_vendedor_sao_consolidadas_e_nome_e_normalizado():
    resultado = calcular_equipe([_linha("Ana", "100", 1, "1"), _linha("  Ana ", "50", 2, "3")], INI, FIM)

    assert len(resultado.vendedores) == 1
    assert resultado.vendedores[0].faturamento_bruto == 150.0
    assert resultado.vendedores[0].atendimentos == 3


def test_loja_usa_atendimentos_informados_quando_existem():
    linhas = [_linha("Ana", "100", 2, "2"), _linha("Bruno", "100", 2, "2")]

    somado = calcular_equipe(linhas, INI, FIM)
    informado = calcular_equipe(linhas, INI, FIM, atendimentos_loja=3)

    assert (somado.loja.atendimentos, somado.loja.atendimentos_somados_por_vendedor) == (4, True)
    assert (informado.loja.atendimentos, informado.loja.atendimentos_somados_por_vendedor) == (3, False)
    assert informado.loja.ticket_medio == round(200 / 3, 2)


def test_variacao_contra_periodo_anterior():
    resultado = calcular_equipe(
        [_linha("Ana", "1200", 10, "20")],
        INI, FIM,
        anteriores=[_linha("Ana", "1000", 10, "10"), _linha("Carla", "500", 5, "5")],
    )

    ana = _por_nome(resultado)["Ana"]
    assert ana.variacao_liquido == 0.2
    assert ana.variacao_ticket_medio == 0.2
    assert ana.variacao_pa == 1.0
    assert resultado.periodo_anterior.fim == date(2026, 8, 31)


def test_vendedor_novo_nao_tem_variacao():
    resultado = calcular_equipe([_linha("Dani", "100", 1, "1")], INI, FIM, anteriores=[_linha("Ana", "1", 1, "1")])

    assert _por_nome(resultado)["Dani"].variacao_liquido is None


def test_divisao_por_zero_vira_zero():
    resultado = calcular_equipe([_linha("Ana", "0", 0, "0")], INI, FIM)

    ana = _por_nome(resultado)["Ana"]
    assert (ana.ticket_medio, ana.pa, ana.preco_medio_peca, ana.participacao) == (0, 0, 0, 0)


@pytest.mark.parametrize("disponiveis, esperado", [
    ({TipoDataset.VENDAS_VENDEDOR_PERIODO}, {"serie_diaria", "mix_categoria", "conversao_contatos"}),
    ({TipoDataset.VENDAS_DIARIAS}, {"mix_categoria", "conversao_contatos"}),
    ({TipoDataset.ITENS_VENDA}, {"conversao_contatos"}),
    ({TipoDataset.ITENS_VENDA, TipoDataset.CONTATOS_VENDEDOR}, set()),
])
def test_indisponivel_depende_do_que_foi_enviado(disponiveis, esperado):
    resultado = calcular_equipe([_linha("Ana", "1", 1, "1")], INI, FIM, tipos_disponiveis=disponiveis)

    assert {i.indicador for i in resultado.indisponivel} == esperado


def test_periodo_anterior_tem_a_mesma_duracao():
    assert periodo_anterior(date(2026, 9, 10), date(2026, 9, 16)) == (date(2026, 9, 3), date(2026, 9, 9))


def test_mesmo_resultado_partindo_de_itens_ou_de_relatorio_por_periodo():
    itens = [
        ItemVenda("V1", INI, Operacao.VENDA, D("2"), D("100"), vendedor="Ana"),
        ItemVenda("V1", INI, Operacao.VENDA, D("1"), D("40"), vendedor="Bruno"),
        ItemVenda("V2", FIM, Operacao.VENDA, D("1"), D("60"), vendedor="Ana"),
        ItemVenda("T1", FIM, Operacao.TROCA, D("1"), D("20"), vendedor="Ana"),
    ]
    relatorio = [_linha("Ana", "160", 2, "3", trocas="20"), _linha("Bruno", "40", 1, "1")]

    de_itens = calcular_equipe(vendedor_periodo(itens, INI, FIM), INI, FIM, atendimentos_loja=atendimentos_da_loja(itens))
    de_relatorio = calcular_equipe(relatorio, INI, FIM, atendimentos_loja=2)

    assert de_itens == de_relatorio


def test_serie_e_mix_de_um_vendedor():
    from vitrine_core.bi.equipe import mix_do_vendedor, serie_do_vendedor
    from vitrine_core.datasets.agregacao import vendas_diarias

    itens = [
        ItemVenda("V1", INI, Operacao.VENDA, D("2"), D("100"), vendedor="Ana", grupo="FEMININO", familia="VESTIDOS"),
        ItemVenda("V2", FIM, Operacao.VENDA, D("1"), D("300"), vendedor="Ana", grupo="FEMININO", familia="CALCAS"),
        ItemVenda("V3", FIM, Operacao.VENDA, D("1"), D("50"), vendedor="Bruno", grupo="MASCULINO", familia="CAMISAS"),
        ItemVenda("V4", FIM, Operacao.VENDA, D("1"), D("10"), vendedor=None, grupo="ACESSORIOS", familia="MEIAS"),
    ]

    serie = serie_do_vendedor(vendas_diarias(itens), "Ana")
    mix = mix_do_vendedor(itens, "Ana")

    assert [(p.data, p.faturamento_bruto, p.pa) for p in serie] == [(INI, 100.0, 2.0), (FIM, 300.0, 1.0)]
    assert [(m.familia, m.participacao) for m in mix] == [("CALCAS", 0.75), ("VESTIDOS", 0.25)]
    assert [m.familia for m in mix_do_vendedor(itens, None)] == ["MEIAS"]
