"""Orçamento de tempo da geração de dados da demonstração.

O consumo pelo BI já está coberto por ``test_bi_large_volume.py``; o que
falta medir é a geração em si. O teto de 180 dias das rotas somado ao
comparativo ano-a-ano faz um único request materializar dois intervalos
grandes — daí o cache por dia.
"""

import time
from datetime import date, timedelta

from app.adapters.demo.transaction_source import DemoTransactionSource

PERIODO_MAXIMO = 180  # limite das rotas de BI


def _periodo():
    fim = date.today() - timedelta(days=1)
    return fim - timedelta(days=PERIODO_MAXIMO - 1), fim


def test_periodo_maximo_gera_em_tempo_aceitavel():
    inicio, fim = _periodo()
    marca = time.perf_counter()
    itens = DemoTransactionSource().get_items(inicio, fim)
    duracao = time.perf_counter() - marca
    assert itens
    assert duracao < 3.0, f"geração fria levou {duracao:.2f}s"


def test_segunda_consulta_aproveita_o_cache():
    inicio, fim = _periodo()
    source = DemoTransactionSource()
    source.get_items(inicio, fim)  # aquece

    marca = time.perf_counter()
    source.get_items(inicio, fim)
    duracao = time.perf_counter() - marca
    assert duracao < 0.5, f"consulta quente levou {duracao:.2f}s"


def test_volume_diario_fica_dentro_do_orcamento():
    """Trava contra alguém subir o volume e travar a demo sem perceber."""
    inicio, fim = _periodo()
    itens = DemoTransactionSource().get_items(inicio, fim)
    por_dia = len(itens) / PERIODO_MAXIMO
    assert por_dia < 600, f"{por_dia:.0f} itens/dia é mais do que o orçado"
