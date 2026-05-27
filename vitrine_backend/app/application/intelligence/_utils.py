"""Utility helpers for the intelligence module."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Retorna datetime UTC naive (compatível com SQLite que não tem timezone)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
