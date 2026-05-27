from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime
from app.infrastructure.db.database import Base


class IntelligenceUsage(Base):
    """Controle de uso mensal (bucket de 10 chamadas/mês)."""
    __tablename__ = "intelligence_usage"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(default="default")
    mes_ano: Mapped[str] = mapped_column()  # "2026-05"
    chamadas_feitas: Mapped[int] = mapped_column(default=0)
    ultima_chamada: Mapped[datetime | None] = mapped_column(DateTime(), default=None)
