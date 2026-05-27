"""Cache SQLite para resultados do Intelligence com TTL de 7 dias."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.domain.models.intelligence_cache import IntelligenceCache

TTL_DIAS = 7


def obter_cache(db: Session, tenant_id: str = "default") -> dict | None:
    """Retorna cache se existir e não expirado."""
    agora = datetime.now(timezone.utc)
    row: IntelligenceCache | None = (
        db.query(IntelligenceCache)
        .filter(
            IntelligenceCache.tenant_id == tenant_id,
            IntelligenceCache.periodo_key == "30d",
        )
        .first()
    )
    if row and row.expira_em and row.expira_em > agora:
        import json
        return json.loads(row.resultado_json)
    return None


def salvar_cache(
    db: Session,
    resultado_dict: dict,
    fonte: str,
    tenant_id: str = "default",
) -> None:
    """Salva ou substitui cache."""
    import json
    agora = datetime.now(timezone.utc)
    expira = agora + timedelta(days=TTL_DIAS)

    row = IntelligenceCache(
        tenant_id=tenant_id,
        periodo_key="30d",
        resultado_json=json.dumps(resultado_dict, default=str),
        fonte=fonte,
        gerado_em=agora,
        expira_em=expira,
    )
    db.merge(row)
    db.commit()


def limpar_expirados(db: Session) -> int:
    """Remove caches expirados. Retorna qtd removida."""
    agora = datetime.now(timezone.utc)
    removidos = (
        db.query(IntelligenceCache)
        .filter(IntelligenceCache.expira_em <= agora)
        .delete()
    )
    db.commit()
    return removidos
