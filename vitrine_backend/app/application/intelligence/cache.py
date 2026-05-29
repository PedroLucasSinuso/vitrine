"""Cache SQLite para resultados do Intelligence com TTL de 7 dias."""
from datetime import date, datetime, timedelta
from app.application.intelligence._utils import utcnow
from sqlalchemy.orm import Session
from app.domain.models.intelligence_cache import IntelligenceCache

TTL_DIAS = 7


def _periodo_key(data_inicio: date, data_fim: date) -> str:
    """Gera chave do período baseada nas datas reais (ex: '90d' ou '2026-03-01_2026-05-29')."""
    delta = (data_fim - data_inicio).days
    if delta <= 30:
        return f"{delta}d"
    return f"{data_inicio.isoformat()}_{data_fim.isoformat()}"


def obter_cache(db: Session, data_inicio: date, data_fim: date, tenant_id: str = "default") -> dict | None:
    """Retorna cache se existir e não expirado."""
    agora = utcnow()
    periodo_key = _periodo_key(data_inicio, data_fim)
    row: IntelligenceCache | None = (
        db.query(IntelligenceCache)
        .filter(
            IntelligenceCache.tenant_id == tenant_id,
            IntelligenceCache.periodo_key == periodo_key,
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
    data_inicio: date,
    data_fim: date,
    tenant_id: str = "default",
) -> None:
    """Salva ou substitui cache."""
    import json
    agora = utcnow()
    expira = agora + timedelta(days=TTL_DIAS)

    row = IntelligenceCache(
        tenant_id=tenant_id,
        periodo_key=_periodo_key(data_inicio, data_fim),
        resultado_json=json.dumps(resultado_dict, default=str),
        fonte=fonte,
        gerado_em=agora,
        expira_em=expira,
    )
    db.merge(row)
    db.commit()


def invalidar_cache_intelligence(db: Session, tenant_id: str = "default") -> None:
    """Remove o cache de inteligência forçando re-análise na próxima requisição.

    Chamado quando configurações relevantes (ex: ignored_groups) são alteradas.
    """
    db.query(IntelligenceCache).filter(
        IntelligenceCache.tenant_id == tenant_id,
    ).delete()
    db.commit()


def limpar_expirados(db: Session) -> int:
    """Remove caches expirados. Retorna qtd removida."""
    agora = utcnow()
    removidos = (
        db.query(IntelligenceCache)
        .filter(IntelligenceCache.expira_em <= agora)
        .delete()
    )
    db.commit()
    return removidos
