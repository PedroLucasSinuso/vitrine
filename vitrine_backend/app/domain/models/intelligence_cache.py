from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class IntelligenceCache(Base):
    """Cache do resultado completo da análise.
    
    TTL de 7 dias. Limpeza lazy no scheduler noturno.
    """
    __tablename__ = "intelligence_cache"

    tenant_id: Mapped[str] = mapped_column(primary_key=True, default="default")
    periodo_key: Mapped[str] = mapped_column(primary_key=True, default="30d")
    resultado_json: Mapped[str] = mapped_column()
    fonte: Mapped[str] = mapped_column()  # "claude" | "gpt4o_mini" | "deterministico"
    gerado_em: Mapped[datetime] = mapped_column()
    expira_em: Mapped[datetime] = mapped_column()
