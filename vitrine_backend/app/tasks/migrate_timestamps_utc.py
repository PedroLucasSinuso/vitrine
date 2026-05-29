"""Migração única: converte timestamps de BRT (hora local) para UTC.

SQLite CURRENT_TIMESTAMP retorna hora local do sistema (BRT, UTC-3),
não UTC como documentado. Todas as colunas DateTime com default=func.now()
foram armazenadas como BRT.

Esta migração adiciona 3 horas a cada timestamp existente,
convertendo de BRT → UTC para alinhar com o novo default=_utcnow()
que usa datetime.utcnow() do Python (sempre UTC).

Tabelas afetadas:
- notificacoes: criada_em, lida_em, resolvida_em
- scheduler_lock: acquired_at, heartbeat_at

Uso:
    uv run python -m app.tasks.migrate_timestamps_utc
"""

import logging
from datetime import timedelta

from sqlalchemy import text

from app.infrastructure.db.database import SessionLocal

logger = logging.getLogger(__name__)

TABELAS = {
    "notificacoes": ["criada_em", "lida_em", "resolvida_em"],
    "scheduler_lock": ["acquired_at", "heartbeat_at"],
}

DELTA_HORAS = 3  # BRT (UTC-3) → UTC


def migrate() -> int:
    """Executa migração. Retorna total de registros alterados."""
    total = 0
    db = SessionLocal()
    try:
        for tabela, colunas in TABELAS.items():
            for coluna in colunas:
                sql = text(
                    f"UPDATE {tabela} "
                    f"SET {coluna} = datetime({coluna}, '+{DELTA_HORAS} hours') "
                    f"WHERE {coluna} IS NOT NULL"
                )
                result = db.execute(sql)
                total += result.rowcount
        db.commit()
        logger.info("Migração concluída: %d registros atualizados", total)
    except Exception:
        logger.exception("Erro na migração de timestamps")
        db.rollback()
        raise
    finally:
        db.close()
    return total


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Iniciando migração BRT → UTC...")
    total = migrate()
    logger.info("Pronto! %d linhas atualizadas.", total)


if __name__ == "__main__":
    main()
