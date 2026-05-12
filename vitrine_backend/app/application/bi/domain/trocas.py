from app.application.bi.schema import COLUNAS
from app.application.bi.domain.fluxo import Fluxo
import logging

logger = logging.getLogger(__name__)


class Trocas(Fluxo):
    def __init__(self, df):
        rows_in = len(df)
        super().__init__(df)
        self.df = self.df[
            (self.df[COLUNAS.cancelado] != "*") &
            (self.df[COLUNAS.operacao] == "E") &
            (self.df[COLUNAS.devolucao].isin(["T", "D"]))
        ].reset_index(drop=True)
        logger.debug("BI Trocas | rows_in=%s rows_apos_filtro=%s", rows_in, len(self.df))