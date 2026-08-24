"""Fonte de transações da demonstração."""

import threading
from datetime import date, datetime, timedelta

from cachetools import LRUCache

from app.adapters.demo import config
from app.adapters.demo.generator import gerar_dia
from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import TransactionItem


class DemoTransactionSource(TransactionSource):
    """Movimentações sintéticas, geradas sob demanda.

    Os dados são função pura da data, então nada é pré-computado: um
    período de 180 dias custa 180 gerações de dia, e o cache abaixo faz os
    requests seguintes reusarem o que já foi gerado.

    ``get_kpi_aggregates`` NÃO é sobrescrito de propósito. Herdando o
    ``None`` da interface, os KPIs passam pelo mesmo caminho de dados dos
    gráficos; um atalho agregado aqui faria o número do topo da tela
    divergir do gráfico logo abaixo dele.
    """

    def __init__(self) -> None:
        self._cache: LRUCache = LRUCache(maxsize=config.MAXSIZE_CACHE_DIAS)
        self._lock = threading.Lock()

    def get_items(self, start: date, end: date) -> list[TransactionItem]:
        if start > end:
            return []

        hoje = date.today()
        primeiro_dia = hoje - timedelta(days=config.JANELA_DIAS)
        # Fora da janela devolve vazio em vez de erro: o BI chama isto com
        # datas deslocadas de um ano para o comparativo, e uma exceção ali
        # derrubaria a tela inteira.
        start = max(start, primeiro_dia)
        end = min(end, hoje)

        itens: list[TransactionItem] = []
        dia = start
        while dia <= end:
            itens.extend(self._itens_do_dia(dia, hoje))
            dia += timedelta(days=1)
        return itens

    def _itens_do_dia(self, dia: date, hoje: date) -> list[TransactionItem]:
        with self._lock:
            cacheados = self._cache.get(dia)
            if cacheados is None:
                cacheados = gerar_dia(dia)
                self._cache[dia] = cacheados

        if dia != hoje:
            return cacheados
        # O dia corrente é parcial: só existe o que já aconteceu até agora.
        # O corte fica FORA do cache porque a hora avança durante o dia — e
        # porque as telas diária e por hora não filtram por conta própria,
        # só o comparativo faz isso.
        hora_atual = datetime.now().hour
        return [i for i in cacheados if i.time is not None and i.time.hour <= hora_atual]

    def invalidar_cache(self) -> None:
        """Descarta os dias em cache."""
        with self._lock:
            self._cache.clear()
