from sqlalchemy import text
from app.application.etl.interfaces import DataSource
from app.infrastructure.db.session import PostgresSession
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)


class PostgresLoader(DataSource):
    def __init__(self, query: str):
        self.query = query

    def load(self) -> list[dict]:
        logger.info("Executando query no Postgres")

        if not PostgresSession:
            raise RuntimeError("PostgreSQL nÃ£o configurado. Verifique as variÃ¡veis de ambiente.")

        with temporizador("PostgresLoader.load", logger):
            with PostgresSession() as session:
                query = self.query.lstrip("\ufeff").strip()
                result = session.execute(text(query))
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
        logger.info("PostgresLoader.load | rows=%s", len(rows))
        return rows