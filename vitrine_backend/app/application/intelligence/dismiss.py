"""Gestão de insights ignorados pelo usuário."""
from datetime import datetime
from app.application.intelligence._utils import utcnow
from sqlalchemy.orm import Session
from app.domain.models.intelligence_dismissed import InsightsDismissed


def dismiss_insight(db: Session, hash: str, tenant_id: str = "default") -> None:
    """Marca insight como ignorado."""
    row = InsightsDismissed(
        hash=hash,
        tenant_id=tenant_id,
        dismissido_em=utcnow(),
    )
    db.merge(row)
    db.commit()


def is_dismissed(db: Session, hash: str, tenant_id: str = "default") -> bool:
    """Verifica se insight já foi ignorado."""
    return (
        db.query(InsightsDismissed)
        .filter(
            InsightsDismissed.hash == hash,
            InsightsDismissed.tenant_id == tenant_id,
        )
        .first()
        is not None
    )


def list_dismissed(db: Session, tenant_id: str = "default") -> set[str]:
    """Retorna set de hashes ignorados."""
    rows = (
        db.query(InsightsDismissed.hash)
        .filter(InsightsDismissed.tenant_id == tenant_id)
        .all()
    )
    return {row[0] for row in rows}
