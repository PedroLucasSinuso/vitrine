"""Controle de custo mensal — bucket de chamadas de IA por tenant."""
from datetime import datetime
from app.application.intelligence._utils import utcnow
from sqlalchemy.orm import Session
from app.domain.models.intelligence_usage import IntelligenceUsage

MAX_CHAMADAS_POR_MES = 10  # configurável via settings


def _mes_ano() -> str:
    return utcnow().strftime("%Y-%m")


def pode_solicitar(db: Session, tenant_id: str = "default", max_calls: int = MAX_CHAMADAS_POR_MES) -> bool:
    """Verifica se o tenant ainda pode fazer chamadas este mês."""
    if max_calls <= 0:
        return False
    mes = _mes_ano()
    row: IntelligenceUsage | None = (
        db.query(IntelligenceUsage)
        .filter(
            IntelligenceUsage.tenant_id == tenant_id,
            IntelligenceUsage.mes_ano == mes,
        )
        .first()
    )
    if row is None:
        return True
    return row.chamadas_feitas < max_calls


def registrar_chamada(db: Session, tenant_id: str = "default") -> None:
    """Incrementa contador de chamadas do mês."""
    mes = _mes_ano()
    agora = utcnow()
    row: IntelligenceUsage | None = (
        db.query(IntelligenceUsage)
        .filter(
            IntelligenceUsage.tenant_id == tenant_id,
            IntelligenceUsage.mes_ano == mes,
        )
        .first()
    )
    if row is None:
        row = IntelligenceUsage(
            tenant_id=tenant_id,
            mes_ano=mes,
            chamadas_feitas=1,
            ultima_chamada=agora,
        )
        db.add(row)
    else:
        row.chamadas_feitas += 1
        row.ultima_chamada = agora
    db.commit()


def chamadas_no_mes(db: Session, tenant_id: str = "default") -> int:
    """Retorna quantas chamadas foram feitas no mês atual."""
    mes = _mes_ano()
    row: IntelligenceUsage | None = (
        db.query(IntelligenceUsage)
        .filter(
            IntelligenceUsage.tenant_id == tenant_id,
            IntelligenceUsage.mes_ano == mes,
        )
        .first()
    )
    if row is None:
        return 0
    return row.chamadas_feitas
