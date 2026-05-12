from dataclasses import dataclass
from app.infrastructure.db.session import SqliteSession
from app.application.etl.extract.extractor import ProdutoExtractor
from app.application.etl.transform.transformer import transformar_produtos
from app.application.etl.load.loader import carregar_produtos, atualizar_cache
from app.application.bi.loader import limpar_cache_bi
from app.core.error_handler import sanitizar_erro, logar_erro_interno
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)


@dataclass
class EtlResult:
    produtos_count: int
    codigos_count: int


def run_etl() -> EtlResult:
    logger.info("Iniciando ETL")

    with temporizador("ETL Pipeline completo", logger):
        extractor = ProdutoExtractor()

        data = extractor.extract()

        logger.info("Extract concluÃ­do | produtos=%s codigos=%s", len(data.produtos), len(data.codigos))

        produtos = transformar_produtos(
            data.produtos,
            data.codigos
        )

        logger.info("Transform concluÃ­do | total=%s", len(produtos))

        with SqliteSession() as session:
            try:
                with session.begin():
                    produtos_count, codigos_count = carregar_produtos(session, produtos)
                    atualizar_cache(session)

                logger.info("Load concluÃ­do com sucesso | produtos=%s codigos=%s", produtos_count, codigos_count)

                limpar_cache_bi()

                return EtlResult(produtos_count=produtos_count, codigos_count=codigos_count)

            except Exception as e:
                logar_erro_interno("Erro no ETL", e)

                session.rollback()
                atualizar_cache(session, status="erro", erro=sanitizar_erro(e))
                session.commit()

                raise RuntimeError("Erro ao carregar dados no SQLite")