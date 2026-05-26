from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class TentativaLogin(Base):
    """Registro de tentativas de login para controle de lockout (S2).

    Cada linha representa uma tentativa de autenticação. Tentativas falhas
    nos últimos 15 minutos são contadas; se >= 5, o login é bloqueado
    temporariamente.
    """

    __tablename__ = "tentativas_login"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    sucesso: Mapped[bool] = mapped_column(Boolean, default=False)
