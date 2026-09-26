from collections import defaultdict
from datetime import date
from decimal import Decimal

from vitrine_core.datasets.tipos import (
    ItemVenda,
    Operacao,
    VendaDiaria,
    VendaProdutoPeriodo,
    VendaVendedorPeriodo,
)

ZERO = Decimal("0")


def _vendedor(nome: str | None) -> str | None:
    nome = (nome or "").strip()
    return nome or None


def atendimentos_da_loja(itens: list[ItemVenda]) -> int:
    return len({i.documento for i in itens if i.operacao == Operacao.VENDA})


def vendas_diarias(itens: list[ItemVenda], por_vendedor: bool = True) -> list[VendaDiaria]:
    grupos: dict[tuple[date, str | None], list[ItemVenda]] = defaultdict(list)
    for item in itens:
        chave_vendedor = _vendedor(item.vendedor) if por_vendedor else None
        grupos[(item.data, chave_vendedor)].append(item)

    resultado = []
    for (dia, vendedor), grupo in sorted(grupos.items(), key=lambda g: (g[0][0], g[0][1] or "")):
        vendas = [i for i in grupo if i.operacao == Operacao.VENDA]
        resultado.append(VendaDiaria(
            data=dia,
            vendedor=vendedor,
            faturamento_bruto=sum((i.valor for i in vendas), ZERO),
            trocas=sum((i.valor for i in grupo if i.operacao == Operacao.TROCA), ZERO),
            atendimentos=len({i.documento for i in vendas}),
            pecas=sum((i.quantidade for i in vendas), ZERO),
        ))
    return resultado


def vendedor_periodo_de_diarias(diarias: list[VendaDiaria], inicio: date, fim: date) -> list[VendaVendedorPeriodo]:
    acumulado: dict[str | None, dict] = defaultdict(
        lambda: {"atendimentos": 0, "pecas": ZERO, "bruto": ZERO, "trocas": ZERO}
    )
    for dia in diarias:
        if not inicio <= dia.data <= fim:
            continue
        linha = acumulado[_vendedor(dia.vendedor)]
        linha["atendimentos"] += dia.atendimentos
        linha["pecas"] += dia.pecas
        linha["bruto"] += dia.faturamento_bruto
        linha["trocas"] += dia.trocas
    return [
        VendaVendedorPeriodo(
            inicio=inicio,
            fim=fim,
            vendedor=vendedor,
            atendimentos=valores["atendimentos"],
            pecas=valores["pecas"],
            faturamento_bruto=valores["bruto"],
            trocas=valores["trocas"],
        )
        for vendedor, valores in acumulado.items()
    ]


def vendedor_periodo(itens: list[ItemVenda], inicio: date, fim: date) -> list[VendaVendedorPeriodo]:
    no_periodo = [i for i in itens if inicio <= i.data <= fim]
    return vendedor_periodo_de_diarias(vendas_diarias(no_periodo), inicio, fim)


def produto_periodo(itens: list[ItemVenda], inicio: date, fim: date) -> list[VendaProdutoPeriodo]:
    acumulado: dict[tuple, dict] = defaultdict(lambda: {"quantidade": ZERO, "receita": ZERO})
    for item in itens:
        if item.operacao != Operacao.VENDA or not inicio <= item.data <= fim:
            continue
        chave = (item.codigo_produto, item.produto, item.grupo, item.familia)
        acumulado[chave]["quantidade"] += item.quantidade
        acumulado[chave]["receita"] += item.valor
    return [
        VendaProdutoPeriodo(
            inicio=inicio, fim=fim, codigo_produto=codigo, produto=produto,
            grupo=grupo, familia=familia, quantidade=v["quantidade"], receita=v["receita"],
        )
        for (codigo, produto, grupo, familia), v in acumulado.items()
    ]
