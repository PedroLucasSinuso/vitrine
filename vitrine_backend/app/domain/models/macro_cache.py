"""SQLAlchemy ORM model for monthly macro indicator cache."""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.infrastructure.db.database import Base


class MacroCache(Base):
    """Monthly macro indicator cache.

    Cache is valid only within the same calendar month.
    Expired entries are ignored at read time and pruned lazily.
    """
    __tablename__ = "macro_cache"

    chave: str = Column(String(50), primary_key=True)
    valor_json: str = Column(Text, nullable=False)  # JSON serialized MacroIndicator
    consultado_em: datetime = Column(DateTime, nullable=False)
    mes_ano: str = Column(String(7), nullable=False)  # "2026-05"
