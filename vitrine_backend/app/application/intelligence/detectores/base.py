"""ABC para detectores de insight."""
from abc import ABC, abstractmethod
from datetime import date
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource


class Detector(ABC):
    """Detector analisa dados brutos e retorna insights estruturados."""

    @abstractmethod
    def detectar(
        self,
        db: Session,
        source: TransactionSource,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        """Retorna lista de dicts serializáveis para o prompt."""
