from datetime import datetime
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.database import Base


class CacheStatus(Base):
    __tablename__ = "cache_status"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="sucesso")
    erro: Mapped[str | None] = mapped_column(String, nullable=True)