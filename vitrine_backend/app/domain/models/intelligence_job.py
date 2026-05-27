from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class IntelligenceJob(Base):
    """Background task tracking para análise em andamento."""
    __tablename__ = "intelligence_jobs"

    id: Mapped[str] = mapped_column(primary_key=True)  # UUID
    tenant_id: Mapped[str] = mapped_column(default="default")
    periodo_key: Mapped[str] = mapped_column(default="30d")
    status: Mapped[str] = mapped_column()  # "processing" | "ready" | "error"
    resultado_hash: Mapped[str | None] = mapped_column(default=None)
    erro: Mapped[str | None] = mapped_column(default=None)
    criado_em: Mapped[datetime] = mapped_column()
    concluido_em: Mapped[datetime | None] = mapped_column(default=None)
