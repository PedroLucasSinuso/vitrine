from app.core.models.transaction import TransactionItem, OperationType
from app.application.bi.domain.fluxo import Fluxo
import logging

logger = logging.getLogger(__name__)


class Trocas(Fluxo):
    def __init__(self, items: list[TransactionItem]):
        rows_in = len(items)
        self.items = [
            i for i in items
            if not i.is_canceled and i.operation == OperationType.RETURN
        ]
        self._df = None
        logger.debug("BI Trocas | rows_in=%s rows_apos_filtro=%s", rows_in, len(self.items))
