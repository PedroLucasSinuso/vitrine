from app.application.bi.schema import COLUNAS, CodigoOperacao
from app.application.bi.domain.fluxo import Fluxo
import logging

logger = logging.getLogger(__name__)


class Consumo(Fluxo):
    def __init__(self, df):
        rows_in = len(df)
        super().__init__(df)
        self.df = self.df[
            (self.df[COLUNAS.cancelado] != "*") &
            (self.df[COLUNAS.operacao] == "S") &
            (self.df[COLUNAS.id_operacao] == CodigoOperacao.CONSUMO_INTERNO) &
            (self.df[COLUNAS.id_nfe].notna())
        ].reset_index(drop=True)
        logger.debug("BI Consumo | rows_in=%s rows_apos_filtro=%s", rows_in, len(self.df))