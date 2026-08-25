"""Aleatoriedade determinística por dia.

A semente sai da data absoluta, nunca de "hoje": o dia 2026-03-14 produz
sempre os mesmos números, seja consultado hoje ou daqui a um ano. É isso
que permite dados estáveis e, ao mesmo tempo, uma janela que acompanha o
calendário.

Usa CRC32 e não ``hash()`` de propósito: ``PYTHONHASHSEED`` randomiza o
hash de strings a cada processo, então dois workers do uvicorn serviriam
números diferentes para a mesma data — os gráficos mudariam a cada F5.
"""

import random
import zlib
from datetime import date

from app.adapters.demo.config import SEED_BASE


def semente(*partes: object) -> int:
    """Semente estável entre processos para uma combinação de valores."""
    texto = ":".join(str(p) for p in (SEED_BASE, *partes))
    return zlib.crc32(texto.encode("utf-8"))


def rng_do_dia(dia: date) -> random.Random:
    """Gerador dedicado a um dia do calendário."""
    return random.Random(semente("dia", dia.isoformat()))
