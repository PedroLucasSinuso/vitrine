from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class TokenBlacklist(Base):
    """Registro de tokens JWT revogados.

    Cada entrada representa um token individual (identificado por ``jti``)
    que foi revogado antes da expiração natural.
    """

    __tablename__ = "token_blacklist"

    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
