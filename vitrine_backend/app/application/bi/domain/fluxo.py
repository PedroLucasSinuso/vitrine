import pandas as pd
from app.core.models.transaction import TransactionItem
from app.application.bi.schema import COLUNAS
import logging

logger = logging.getLogger(__name__)


class Fluxo:
    """Classe base para domínios de fluxo de mercadorias.

    Opera em list[TransactionItem] (em vez de pd.DataFrame).
    Mantém .df property para compatibilidade com módulos de reporting.
    """

    # Colunas esperadas pelo reporting — garante DataFrame vazio com schema correto
    _COLUMNS = [
        COLUNAS.id_documento, COLUNAS.emissao, COLUNAS.hora,
        COLUNAS.operacao, COLUNAS.cancelado, COLUNAS.total_documento,
        COLUNAS.grupo, COLUNAS.familia, COLUNAS.codigo, COLUNAS.produto,
        COLUNAS.qtd_item, COLUNAS.receita,
    ]

    def __init__(self, items: list[TransactionItem]):
        self.items: list[TransactionItem] = items
        self._df: pd.DataFrame | None = None

    @property
    def df(self) -> pd.DataFrame:
        """Compatibilidade retroativa com módulos de reporting.
        Converte self.items para DataFrame usando COLUNAS.
        Garante que DataFrame vazio tenha as colunas esperadas.
        """
        if self._df is None:
            dicts = [self._to_dict(i) for i in self.items]
            if dicts:
                self._df = pd.DataFrame(dicts)
            else:
                self._df = pd.DataFrame(columns=self._COLUMNS)
        return self._df

    @staticmethod
    def _to_dict(item: TransactionItem) -> dict:
        return {
            COLUNAS.id_documento: item.document_id,
            COLUNAS.emissao: item.date,
            COLUNAS.hora: item.time,
            COLUNAS.operacao: item.operation.value if item.operation else "",
            COLUNAS.cancelado: "",
            COLUNAS.total_documento: float(item.document_total),
            COLUNAS.grupo: item.group_name,
            COLUNAS.familia: item.family_name,
            COLUNAS.codigo: item.product_code,
            COLUNAS.produto: item.product_name,
            COLUNAS.qtd_item: float(item.quantity),
            COLUNAS.receita: float(item.line_total),
        }
