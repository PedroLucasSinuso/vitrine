"""Filtros compartilhados entre detectores do Intelligence."""
import logging
from sqlalchemy.orm import Session
from app.application.config_service import get as get_config

logger = logging.getLogger(__name__)


def get_ignored_groups(db: Session) -> set[str]:
    """Retorna set de nomes de grupo (upper case) que devem ser ignorados
    em todas as análises do Intelligence.

    Lê da config ``ignored_groups`` no SQLite (config_service).
    Se não existir, retorna set vazio (nada é ignorado).
    O administrador configura essa lista na UI de Configurações > Intelligence.
    """
    raw = get_config(db, "ignored_groups", "")
    if not raw:
        return set()
    grupos = {g.strip().upper() for g in raw.split(",") if g.strip()}
    return grupos


def filtrar_por_grupo(
    resultados: list[dict],
    grupos_ignorados: set[str],
    chave_grupo: str = "grupo",
) -> list[dict]:
    """Remove resultados cujo grupo está na blacklist."""
    if not grupos_ignorados:
        return resultados
    return [r for r in resultados if r.get(chave_grupo, "").strip().upper() not in grupos_ignorados]
