"""Modelo para lock do scheduler via SQLite.

Substitui o antigo lock por PID file (.scheduler.lock).
Mais robusto: auto-expira, visível via SQL, funciona em qualquer SO.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.infrastructure.db.database import Base

STALE_TIMEOUT_MINUTES = 10


def _utcnow() -> datetime:
    """Retorna datetime UTC naive para armazenamento consistente."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SchedulerLock(Base):
    __tablename__ = "scheduler_lock"

    id = Column(Integer, primary_key=True, default=1)  # singleton — sempre 1
    pid = Column(Integer, nullable=False)
    hostname = Column(String(128), nullable=False, default="")
    acquired_at = Column(DateTime, default=_utcnow)
    heartbeat_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    @property
    def is_stale(self) -> bool:
        """Lock expirou se heartbeat está parado há mais de STALE_TIMEOUT."""
        if self.heartbeat_at is None:
            return True
        age = datetime.now(timezone.utc) - self.heartbeat_at.replace(tzinfo=timezone.utc)
        return age > timedelta(minutes=STALE_TIMEOUT_MINUTES)
