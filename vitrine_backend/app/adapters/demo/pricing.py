"""Preço, custo e estoque de um SKU numa data.

Compartilhado entre o gerador de transações e o ``DemoProductSource`` de
propósito: se cada um inventasse o seu preço, a receita do BI não bateria
com a tabela de preços da tela de produtos — e é exatamente esse tipo de
incoerência que denuncia um dado falso.

Tudo é função determinística de (SKU, data): não há estado nem sorteio a
cada chamada.
"""

import random
from datetime import date
from decimal import Decimal

from app.adapters.demo.catalog import SkuDemo
from app.adapters.demo.rng import semente

# Variação máxima do preço em torno do valor base, ao longo dos meses.
_VARIACAO_MENSAL = 0.10


def _fator_do_mes(sku: SkuDemo, dia: date) -> float:
    """Deriva de preço daquele SKU naquele mês (estável dentro do mês)."""
    rng = random.Random(semente("preco", sku.internal_code, dia.year, dia.month))
    return rng.uniform(1 - _VARIACAO_MENSAL, 1 + _VARIACAO_MENSAL)


def _arredondar_comercial(valor: Decimal) -> Decimal:
    """Puxa o preço para uma terminação comercial (.90 ou .99)."""
    centavos = valor.quantize(Decimal("0.01"))
    inteiro = int(centavos)
    resto = centavos - inteiro
    if resto < Decimal("0.45"):
        return Decimal(inteiro) + Decimal("0.29") if inteiro else Decimal("0.99")
    if resto < Decimal("0.75"):
        return Decimal(inteiro) + Decimal("0.59")
    return Decimal(inteiro) + Decimal("0.90")


def preco_no_dia(sku: SkuDemo, dia: date) -> Decimal:
    """Preço de venda praticado naquela data."""
    bruto = sku.preco_base * Decimal(str(_fator_do_mes(sku, dia)))
    return _arredondar_comercial(bruto)


def custo_no_dia(sku: SkuDemo, dia: date) -> Decimal:
    """Custo de reposição naquela data, mantendo a margem do grupo."""
    proporcao = sku.custo_base / sku.preco_base
    return (preco_no_dia(sku, dia) * proporcao).quantize(Decimal("0.01"))


def estoque_no_dia(sku: SkuDemo, dia: date) -> float:
    """Saldo em estoque naquela data.

    Alguns SKUs ficam zerados ou negativos de propósito — é o que a tela de
    inventário precisa mostrar para ter graça (divergência de contagem).
    """
    rng = random.Random(semente("estoque", sku.internal_code, dia.isoformat()))
    sorteio = rng.random()
    if sorteio < 0.04:
        return 0.0
    if sorteio < 0.06:
        return round(rng.uniform(-8, -1), 3)
    teto = 40 if sku.por_peso else 220
    return round(rng.uniform(1, teto), 3 if sku.por_peso else 0)


def ativo(sku: SkuDemo) -> bool:
    """~3% do catálogo fica inativo, como em qualquer cadastro real."""
    return random.Random(semente("ativo", sku.internal_code)).random() > 0.03
