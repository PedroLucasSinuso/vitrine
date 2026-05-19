from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from app.application.etl.interfaces import DataSource
from app.application.config_service import montar_url_postgres
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)


def _criar_sessionmaker(db: Session) -> sessionmaker | None:
    """Cria um sessionmaker para o PostgreSQL a partir das configs do ERP."""
    url = montar_url_postgres(db)
    if not url:
        logger.warning("ERP não configurado — PostgreSQL indisponível")
        return None
    engine = create_engine(url, pool_pre_ping=True, pool_size=2, max_overflow=3)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


class PostgresLoader(DataSource):
    """Carrega dados do PostgreSQL usando uma session factory dinâmica.

    A URL de conexão é obtida via ConfigService (montar_url_postgres),
    permitindo que o admin altere as credenciais do ERP pela UI sem
    reiniciar a aplicação.
    """

    def __init__(self, query: str, db: Session):
        self.query = query
        self._sessionmaker = _criar_sessionmaker(db)

    def load(self) -> list[dict]:
        logger.info("Executando query no Postgres")

        if not self._sessionmaker:
            raise RuntimeError("PostgreSQL não configurado. Configure os campos de ERP em Admin > Configurações.")

        with temporizador("PostgresLoader.load", logger):
            with self._sessionmaker() as session:
                query = self.query.lstrip("\ufeff").strip()
                result = session.execute(text(query))
                columns = result.keys()
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
        logger.info("PostgresLoader.load | rows=%s", len(rows))
        return rows