import pandas as pd
from app.application.bi.schema import COLUNAS
import logging

logger = logging.getLogger(__name__)


class Fluxo:
    def __init__(self, df: pd.DataFrame):
        rows_in = len(df)
        self.df = self._padronizar(df.copy())
        logger.debug("BI Fluxo.init | rows_in=%s rows_out=%s", rows_in, len(self.df))

    def _padronizar(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.strip().str.lower()
        df[COLUNAS.receita] = pd.to_numeric(df[COLUNAS.receita], errors="coerce").fillna(0.0)
        df[COLUNAS.qtd_item] = pd.to_numeric(df[COLUNAS.qtd_item], errors="coerce").fillna(0.0)
        return df