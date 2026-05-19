from app.application.etl.dto import ExtractResult, ProdutoRow, CodigoRow
from app.application.etl.query_loader import QueryLoader
from app.infrastructure.postgres.loader import PostgresLoader
from app.core.timer import temporizador
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ProdutoExtractor:
    def __init__(self, db: Session):
        self.produto_loader = PostgresLoader(QueryLoader.load("produto"), db)
        self.codigo_loader = PostgresLoader(QueryLoader.load("codigo"), db)

    def extract(self) -> ExtractResult:
        logger.info("Extraindo dados do Postgres")

        with temporizador("ETL Extract produtos", logger):
            produtos_raw = self.produto_loader.load()
        logger.info("ETL Extract produtos | rows=%s", len(produtos_raw))

        with temporizador("ETL Extract codigos", logger):
            codigos_raw = self.codigo_loader.load()
        logger.info("ETL Extract codigos | rows=%s", len(codigos_raw))

        produtos = [
            ProdutoRow(**row)
            for row in produtos_raw
        ]

        codigos = [
            CodigoRow(**row)
            for row in codigos_raw
            if row["codigo"]
        ]

        return ExtractResult(
            produtos=produtos,
            codigos=codigos,
        )