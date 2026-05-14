from datetime import date
import pandas as pd
from cachetools import TTLCache
from sqlalchemy import text
from app.application.bi.query_loader import BiQueryLoader
from app.application.bi.db import get_bi_engine
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)

MAX_RANGE_DIAS = 366

_bi_cache: TTLCache = TTLCache(maxsize=32, ttl=3600)


def _validar_periodo(data_inicio: date, data_fim: date) -> None:
    if data_fim < data_inicio:
        raise ValueError("data_fim não pode ser anterior a data_inicio")
    if (data_fim - data_inicio).days > MAX_RANGE_DIAS:
        raise ValueError(f"Range máximo permitido é {MAX_RANGE_DIAS} dias")


def carregar_fluxo(data_inicio: date, data_fim: date) -> pd.DataFrame:
    _validar_periodo(data_inicio, data_fim)
    key = (data_inicio.isoformat(), data_fim.isoformat())
    if key in _bi_cache:
        logger.info("BI cache hit | periodo=%s..%s", data_inicio, data_fim)
        return _bi_cache[key]
    sql = BiQueryLoader.load("fluxo")
    with temporizador(f"BI Load fluxo | periodo={data_inicio}..{data_fim}", logger):
        with get_bi_engine().connect() as conn:
            df = pd.read_sql(
                text(sql),
                conn,
                params={
                    "data_inicio": data_inicio.isoformat(),
                    "data_fim": data_fim.isoformat(),
                },
            )
    logger.info("BI Load fluxo | periodo=%s..%s rows=%s", data_inicio, data_fim, len(df))
    _bi_cache[key] = df
    return df


def limpar_cache_bi() -> None:
    _bi_cache.clear()
    logger.info("BI cache limpo")