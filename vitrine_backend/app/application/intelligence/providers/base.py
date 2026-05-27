"""ABC para provedores de IA do Intelligence."""
from abc import ABC, abstractmethod
from app.schemas.intelligence_schema import IntelligenceResponse


class IntelligenceProvider(ABC):
    """Provider de IA que sintetiza insights em texto estratégico."""

    @abstractmethod
    def sintetizar(
        self,
        dados_macro: dict,
        dados_detectores: dict,
    ) -> IntelligenceResponse:
        """Envia prompt + dados para o modelo e retorna resposta estruturada."""
