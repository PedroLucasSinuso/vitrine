from datetime import date
from decimal import Decimal as D

from vitrine_core.datasets.agregacao import (
    atendimentos_da_loja,
    produto_periodo,
    vendas_diarias,
    vendedor_periodo,
    vendedor_periodo_de_diarias,
)
from vitrine_core.datasets.conversao import itens_de_transacoes
from vitrine_core.datasets.tipos import ItemVenda, Operacao
from vitrine_core.models.transaction import OperationType, TransactionItem

SET1, SET2 = date(2026, 9, 1), date(2026, 9, 2)


def _venda(doc, dia, valor, qtd="1", vendedor="Ana", produto="Camisa"):
    return ItemVenda(documento=doc, data=dia, operacao=Operacao.VENDA, quantidade=D(qtd),
                     valor=D(valor), vendedor=vendedor, produto=produto)


def _troca(doc, dia, valor, vendedor="Ana"):
    return ItemVenda(documento=doc, data=dia, operacao=Operacao.TROCA, quantidade=D("1"),
                     valor=D(valor), vendedor=vendedor)


ITENS = [
    _venda("V1", SET1, "100.00", "2"),
    _venda("V1", SET1, "50.00", "1", vendedor="Bruno"),
    _venda("V2", SET1, "80.00", "1", vendedor="Bruno"),
    _venda("V3", SET2, "200.00", "3"),
    _troca("T1", SET2, "30.00"),
    _venda("V4", SET2, "40.00", "1", vendedor="  "),
]


def _por_vendedor(linhas):
    return {l.vendedor: l for l in linhas}


def test_vendedor_periodo_soma_por_vendedor_e_conta_atendimento_compartilhado_para_cada_um():
    linhas = _por_vendedor(vendedor_periodo(ITENS, SET1, SET2))

    assert linhas["Ana"].faturamento_bruto == D("300.00")
    assert linhas["Ana"].trocas == D("30.00")
    assert linhas["Ana"].atendimentos == 2
    assert linhas["Ana"].pecas == D("5")
    assert linhas["Bruno"].atendimentos == 2
    assert linhas[None].faturamento_bruto == D("40.00")


def test_atendimentos_da_loja_conta_documentos_distintos():
    assert atendimentos_da_loja(ITENS) == 4


def test_caminho_por_diarias_da_o_mesmo_resultado_que_direto_dos_itens():
    direto = _por_vendedor(vendedor_periodo(ITENS, SET1, SET2))
    via_diarias = _por_vendedor(vendedor_periodo_de_diarias(vendas_diarias(ITENS), SET1, SET2))

    assert direto == via_diarias


def test_diarias_respeitam_o_periodo_pedido():
    linhas = _por_vendedor(vendedor_periodo(ITENS, SET2, SET2))

    assert linhas["Ana"].faturamento_bruto == D("200.00")
    assert "Bruno" not in linhas


def test_diarias_sem_separar_vendedor():
    diarias = vendas_diarias(ITENS, por_vendedor=False)

    assert [(d.data, d.faturamento_bruto, d.atendimentos) for d in diarias] == [
        (SET1, D("230.00"), 2),
        (SET2, D("240.00"), 2),
    ]


def test_produto_periodo_ignora_trocas():
    linhas = {l.produto: l for l in produto_periodo(ITENS, SET1, SET2)}

    assert linhas["Camisa"].receita == D("470.00")
    assert linhas["Camisa"].quantidade == D("8")


def test_conversao_de_transacoes_ignora_cancelado_perda_e_consumo():
    base = dict(date=SET1, product_code="P1", quantity=D("1"))
    transacoes = [
        TransactionItem(document_id="1", operation=OperationType.SALE, line_total=D("10"), **base),
        TransactionItem(document_id="2", operation=OperationType.SALE, line_total=D("10"), is_canceled=True, **base),
        TransactionItem(document_id="3", operation=OperationType.RETURN, line_total=D("-5"), **base),
        TransactionItem(document_id="4", operation=OperationType.LOSS, line_total=D("7"), **base),
        TransactionItem(document_id="5", operation=OperationType.CONSUMPTION, line_total=D("7"), **base),
    ]

    itens = itens_de_transacoes(transacoes)

    assert [(i.documento, i.operacao, i.valor) for i in itens] == [
        ("1", Operacao.VENDA, D("10")),
        ("3", Operacao.TROCA, D("5")),
    ]
    assert all(i.vendedor is None for i in itens)
