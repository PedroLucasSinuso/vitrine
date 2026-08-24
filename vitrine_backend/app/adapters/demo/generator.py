"""Geração das transações de um dia.

Núcleo do adapter de demonstração. Recebe uma data e devolve os
``TransactionItem`` daquele dia — vendas, trocas, perdas e consumo interno.

Depende só de ``app.core.models``: nada de banco, nada de configuração.
Isso mantém o gerador testável isoladamente e impossível de confundir com
uma fonte de dados real.

Três invariantes que o BI exige e que são fáceis de quebrar:

1. ``document_total`` precisa ser IGUAL em todas as linhas de um mesmo
   documento — o ticket médio sai de ``groupby(documento).first()``. Por
   isso o ticket é montado em duas passadas: linhas primeiro, total depois.
2. ``document_id`` nunca pode se repetir entre dias, senão uma série de
   vários dias funde tickets diferentes no mesmo agrupamento.
3. ``time`` nunca pode ser ``None`` — a análise por hora usa os dois
   primeiros caracteres do horário como rótulo do balde.
"""

import random
from datetime import date, time
from decimal import Decimal

from app.adapters.demo import config, seasonality
from app.adapters.demo.catalog import CATALOGO, PESOS_POPULARIDADE, SkuDemo
from app.adapters.demo.pricing import preco_no_dia
from app.adapters.demo.rng import rng_do_dia
from app.core.models.transaction import OperationType, TransactionItem

# Grupos com maior perda natural (perecíveis) e maior consumo interno.
_GRUPOS_PERECIVEIS = ("HORTIFRUTI", "ACOUGUE", "PADARIA", "LATICINIOS")
_GRUPOS_CONSUMO = ("LIMPEZA", "HIGIENE", "BAZAR", "PADARIA")

_CENTAVOS = Decimal("0.01")


def _sortear_horario(rng: random.Random) -> time:
    horas, pesos = seasonality.horas_e_pesos()
    hora = rng.choices(horas, weights=pesos, k=1)[0]
    return time(hora, rng.randrange(60))


def _sortear_quantidade(rng: random.Random, sku: SkuDemo) -> Decimal:
    if sku.por_peso:
        return Decimal(str(round(rng.uniform(0.2, 2.5), 3)))
    return Decimal(rng.choices([1, 2, 3], weights=[0.72, 0.20, 0.08], k=1)[0])


def _sortear_itens_do_ticket(rng: random.Random) -> int:
    """Quantos SKUs distintos no ticket — geométrica truncada."""
    n = 1
    while n < config.ITENS_TICKET_MAX and rng.random() < 1 - 1 / config.ITENS_TICKET_MODA:
        n += 1
    return max(config.ITENS_TICKET_MIN, n)


def _skus_do_ticket(rng: random.Random, quantidade: int) -> list[SkuDemo]:
    """SKUs distintos, ponderados pela popularidade."""
    escolhidos: dict[str, SkuDemo] = {}
    for _ in range(quantidade * 3):  # tentativas extras cobrem repetições
        if len(escolhidos) == quantidade:
            break
        sku = rng.choices(CATALOGO, weights=PESOS_POPULARIDADE, k=1)[0]
        escolhidos.setdefault(sku.internal_code, sku)
    return list(escolhidos.values())


def _montar_documento(
    document_id: str,
    dia: date,
    horario: time,
    operacao: OperationType,
    linhas: list[tuple[SkuDemo, Decimal, Decimal]],
    is_canceled: bool = False,
    external_document_id: str | None = None,
) -> list[TransactionItem]:
    """Fecha um documento com o total consistente em todas as suas linhas.

    O total só existe depois de somar as linhas, e ``TransactionItem`` é
    imutável — daí montar as linhas como tuplas primeiro e só então
    instanciar.
    """
    total = sum((valor for _, _, valor in linhas), Decimal("0")).quantize(_CENTAVOS)
    return [
        TransactionItem(
            document_id=document_id,
            date=dia,
            time=horario,
            operation=operacao,
            is_canceled=is_canceled,
            product_code=sku.internal_code,
            product_name=sku.nome,
            group_name=sku.grupo,
            family_name=sku.familia,
            quantity=qtd,
            line_total=valor,
            document_total=total,
            external_document_id=external_document_id,
        )
        for sku, qtd, valor in linhas
    ]


def _gerar_vendas(rng: random.Random, dia: date) -> list[TransactionItem]:
    fator = seasonality.fator_do_dia(dia)
    if fator <= 0:
        return []  # loja fechada (feriado)

    n_tickets = round(config.TICKETS_DIA_BASE * fator * rng.gauss(1.0, 0.08))
    itens: list[TransactionItem] = []
    for n in range(max(0, n_tickets)):
        skus = _skus_do_ticket(rng, _sortear_itens_do_ticket(rng))
        linhas = []
        for sku in skus:
            qtd = _sortear_quantidade(rng, sku)
            valor = (preco_no_dia(sku, dia) * qtd).quantize(_CENTAVOS)
            linhas.append((sku, qtd, valor))
        itens.extend(
            _montar_documento(
                # Prefixado com a data: IDs jamais colidem entre dias.
                document_id=f"V{dia:%Y%m%d}{n:05d}",
                dia=dia,
                horario=_sortear_horario(rng),
                operacao=OperationType.SALE,
                linhas=linhas,
                is_canceled=rng.random() < config.TAXA_CANCELAMENTO,
            )
        )
    return itens


def _gerar_trocas(
    rng: random.Random, dia: date, vendas: list[TransactionItem]
) -> list[TransactionItem]:
    """Devoluções do dia, como documentos próprios de valor negativo."""
    faturamento = sum(
        (i.line_total for i in vendas if not i.is_canceled), Decimal("0")
    )
    if faturamento <= 0:
        return []

    alvo = faturamento * Decimal(str(config.TAXA_TROCA))
    itens: list[TransactionItem] = []
    acumulado = Decimal("0")
    n = 0
    while acumulado < alvo and n < 40:
        sku = rng.choices(CATALOGO, weights=PESOS_POPULARIDADE, k=1)[0]
        qtd = _sortear_quantidade(rng, sku)
        valor = (preco_no_dia(sku, dia) * qtd).quantize(_CENTAVOS)
        itens.extend(
            _montar_documento(
                document_id=f"T{dia:%Y%m%d}{n:03d}",
                dia=dia,
                horario=_sortear_horario(rng),
                operacao=OperationType.RETURN,
                linhas=[(sku, qtd, -valor)],
            )
        )
        acumulado += valor
        n += 1
    return itens


def _gerar_movimentos(
    rng: random.Random,
    dia: date,
    operacao: OperationType,
    faixa: tuple[int, int],
    grupos: tuple[str, ...],
    prefixo_doc: str,
    prefixo_externo: str,
) -> list[TransactionItem]:
    """Perdas ou consumo interno — mesma forma, grupos e volumes diferentes.

    Parte dos documentos sai SEM ``external_document_id``: os domínios de
    Perdas e Consumo descartam esses, e é bom que a demo exercite o filtro.
    """
    candidatos = [s for s in CATALOGO if s.grupo in grupos] or list(CATALOGO)
    itens: list[TransactionItem] = []
    for n in range(rng.randint(*faixa)):
        linhas = []
        for _ in range(rng.randint(1, 4)):
            sku = rng.choice(candidatos)
            qtd = _sortear_quantidade(rng, sku)
            valor = (preco_no_dia(sku, dia) * qtd).quantize(_CENTAVOS)
            linhas.append((sku, qtd, valor))
        com_documento = rng.random() >= config.TAXA_SEM_DOCUMENTO
        itens.extend(
            _montar_documento(
                document_id=f"{prefixo_doc}{dia:%Y%m%d}{n:03d}",
                dia=dia,
                horario=_sortear_horario(rng),
                operacao=operacao,
                linhas=linhas,
                external_document_id=(
                    f"{prefixo_externo}{dia:%y%m%d}{n:03d}" if com_documento else None
                ),
            )
        )
    return itens


def gerar_dia(dia: date) -> list[TransactionItem]:
    """Todas as movimentações de mercadoria daquele dia."""
    rng = rng_do_dia(dia)
    vendas = _gerar_vendas(rng, dia)
    if not vendas:
        return []
    return [
        *vendas,
        *_gerar_trocas(rng, dia, vendas),
        *_gerar_movimentos(
            rng, dia, OperationType.LOSS, config.PERDAS_DOCS_DIA,
            _GRUPOS_PERECIVEIS, "P", "AV",
        ),
        *_gerar_movimentos(
            rng, dia, OperationType.CONSUMPTION, config.CONSUMO_DOCS_DIA,
            _GRUPOS_CONSUMO, "C", "CI",
        ),
    ]
