from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class InsightsDismissed(Base):
    """Insights ignorados pelo usuário."""
    __tablename__ = "intelligence_insights_dismissed"

    hash: Mapped[str] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(default="default")
    dismissido_em: Mapped[datetime] = mapped_column()
