from collections import defaultdict
from decimal import Decimal

from pydantic import BaseModel

from vitrine_core.datasets.tipos import ItemVenda, Operacao

ZERO = Decimal("0")
SEM_INFORMACAO = "Não informado"
ORDEM_TAMANHOS = ["PP", "P", "M", "G", "GG", "XG", "XGG", "U"]


class ItemGrade(BaseModel):
    rotulo: str
    quantidade: float
    receita: float
    participacao: float


class CelulaGrade(BaseModel):
    tamanho: str
    cor: str
    quantidade: float


class ResultadoGrade(BaseModel):
    por_tamanho: list[ItemGrade]
    por_cor: list[ItemGrade]
    matriz: list[CelulaGrade]
    tamanhos: list[str]
    cores: list[str]
    grupos: list[str]
    familias: list[str]
    total_pecas: float


def _ordem_tamanho(tamanho: str) -> tuple:
    if tamanho in ORDEM_TAMANHOS:
        return (0, ORDEM_TAMANHOS.index(tamanho), "")
    if tamanho.isdigit():
        return (1, int(tamanho), "")
    return (2, 0, tamanho)


def _resumo(acumulado: dict[str, dict], total: Decimal) -> list[ItemGrade]:
    return [
        ItemGrade(
            rotulo=rotulo,
            quantidade=float(v["quantidade"]),
            receita=round(float(v["receita"]), 2),
            participacao=round(float(v["quantidade"] / total), 4) if total else 0.0,
        )
        for rotulo, v in acumulado.items()
    ]


def calcular_grade(itens: list[ItemVenda], grupo: str | None = None, familia: str | None = None) -> ResultadoGrade:
    vendas = [i for i in itens if i.operacao == Operacao.VENDA]
    grupos = sorted({i.grupo for i in vendas if i.grupo})
    familias = sorted({i.familia for i in vendas if i.familia and (not grupo or i.grupo == grupo)})
    filtrados = [i for i in vendas if (not grupo or i.grupo == grupo) and (not familia or i.familia == familia)]

    por_tamanho: dict[str, dict] = defaultdict(lambda: {"quantidade": ZERO, "receita": ZERO})
    por_cor: dict[str, dict] = defaultdict(lambda: {"quantidade": ZERO, "receita": ZERO})
    matriz: dict[tuple[str, str], Decimal] = defaultdict(lambda: ZERO)
    for item in filtrados:
        tamanho = item.tamanho.strip() or SEM_INFORMACAO
        cor = item.cor.strip() or SEM_INFORMACAO
        for alvo, chave in ((por_tamanho, tamanho), (por_cor, cor)):
            alvo[chave]["quantidade"] += item.quantidade
            alvo[chave]["receita"] += item.valor
        matriz[(tamanho, cor)] += item.quantidade

    total = sum((v["quantidade"] for v in por_tamanho.values()), ZERO)
    tamanhos = sorted(por_tamanho, key=_ordem_tamanho)
    cores = sorted(por_cor, key=lambda c: -por_cor[c]["quantidade"])
    resumo_tamanho = {t: por_tamanho[t] for t in tamanhos}
    resumo_cor = {c: por_cor[c] for c in cores}
    return ResultadoGrade(
        por_tamanho=_resumo(resumo_tamanho, total),
        por_cor=_resumo(resumo_cor, total),
        matriz=[CelulaGrade(tamanho=t, cor=c, quantidade=float(q)) for (t, c), q in matriz.items()],
        tamanhos=tamanhos,
        cores=cores,
        grupos=grupos,
        familias=familias,
        total_pecas=float(total),
    )
