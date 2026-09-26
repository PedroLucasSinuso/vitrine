from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.database import Base


class CacheStatus(Base):
    __tablename__ = "cache_status"
    __table_args__ = (
        Index("ix_cache_status_empresa_last_updated", "empresa_id", "last_updated"),
        CheckConstraint("status IN ('sucesso', 'erro')", name="ck_cache_status_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="sucesso")
    erro: Mapped[str | None] = mapped_column(String, nullable=True)