from abc import ABC, abstractmethod
from datetime import date, datetime

from app.core.models.product import Product
from app.core.models.transaction import TransactionItem


class ProductSource(ABC):
    """Fonte de dados de produtos. Implementado por cada adapter de ERP."""

    @abstractmethod
    def get_all_products(self) -> list[Product]:
        """Retorna todos os produtos disponíveis.
        O adapter é responsável por filtrar apenas produtos ativos/utilizáveis.
        Para ERPs com muitos produtos, considerar paginação interna.
        """
        ...

    def get_products_updated_since(self, since: datetime) -> list[Product]:
        """Opcional: incremental. Útil para ERPs com 50k+ produtos.
        Implementação padrão chama get_all_products() — o adapter pode sobrescrever.
        """
        return self.get_all_products()


class TransactionSource(ABC):
    """Fonte de dados de transações (fluxo de mercadorias)."""

    @abstractmethod
    def get_items(self, start: date, end: date) -> list[TransactionItem]:
        """Retorna todos os itens de documento no período [start, end] (inclusivo).
        Já classificados com OperationType adequado.
        external_document_id = None quando não houver documento comprobatório.
        """
        ...
