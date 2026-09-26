from datetime import date
from decimal import Decimal as D

from vitrine_core.bi.grade import SEM_INFORMACAO, calcular_grade
from vitrine_core.datasets.tipos import ItemVenda, Operacao

DIA = date(2026, 9, 1)


def _item(tamanho, cor, qtd="1", valor="100", grupo="FEMININO", familia="VESTIDOS", operacao=Operacao.VENDA):
    return ItemVenda("1", DIA, operacao, D(qtd), D(valor), grupo=grupo, familia=familia, tamanho=tamanho, cor=cor)


ITENS = [
    _item("M", "Preto", "2", "200"),
    _item("P", "Preto"),
    _item("GG", "Azul"),
    _item("40", "Azul", grupo="CALCADOS", familia="TENIS"),
    _item("38", "Preto", grupo="CALCADOS", familia="TENIS"),
    _item("M", "Preto", operacao=Operacao.TROCA),
    _item("", ""),
]


def test_tamanhos_em_ordem_de_grade_e_numeros_depois():
    resultado = calcular_grade(ITENS)

    assert resultado.tamanhos == ["P", "M", "GG", "38", "40", SEM_INFORMACAO]


def test_trocas_nao_entram_e_matriz_fecha_com_o_total():
    resultado = calcular_grade(ITENS)

    assert resultado.total_pecas == 7
    assert sum(c.quantidade for c in resultado.matriz) == resultado.total_pecas
    assert {c.rotulo: c.quantidade for c in resultado.por_cor} == {"Preto": 4, "Azul": 2, SEM_INFORMACAO: 1}


def test_filtro_por_grupo_e_familia():
    resultado = calcular_grade(ITENS, grupo="CALCADOS", familia="TENIS")

    assert resultado.tamanhos == ["38", "40"]
    assert resultado.familias == ["TENIS"]
    assert resultado.grupos == ["CALCADOS", "FEMININO"]


def test_participacao_por_tamanho():
    resultado = calcular_grade(ITENS)

    assert {i.rotulo: i.participacao for i in resultado.por_tamanho}["M"] == round(2 / 7, 4)
