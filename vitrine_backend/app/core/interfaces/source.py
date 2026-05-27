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

    def get_kpi_aggregates(self, start: date, end: date) -> dict | None:
        """Opcional: retorna agregados de KPI para o período sem carregar linhas.

        Retorna dict com chaves:
            faturamento_bruto (float)
            total_trocas (float)
            qtd_tickets (int)
            ticket_medio (float)
            itens_por_ticket (float)

        Retorna None se o adapter não suportar consulta agregada.
        Implementação padrão retorna None — o adapter pode sobrescrever.
        """
        return None

    def get_dimensao_aggregates(self, start: date, end: date, dimensao: str, metrica: str) -> list[dict] | None:
        """Opcional: retorna agregados por dimensão (produto/grupo/família).
        metrica: 'receita' ou 'quantidade'.
        Retorna None se não suportado."""
        return None

    def get_diario_aggregates(self, start: date, end: date, metrica: str) -> list[dict] | None:
        """Opcional: retorna série temporal diária.
        metrica: 'receita' ou 'quantidade'.
        Retorna None se não suportado."""
        return None

    def get_curva_abc_aggregates(self, start: date, end: date, dimensao: str) -> list[dict] | None:
        """Opcional: retorna dados para curva ABC (receita por dimensão).
        Retorna None se não suportado."""
        return None

    def get_hora_aggregates(self, start: date, end: date, metrica: str) -> list[dict] | None:
        """Opcional: retorna agregados por hora do dia.
        metrica: 'receita' ou 'quantidade'.
        Retorna None se não suportado."""
        return None
