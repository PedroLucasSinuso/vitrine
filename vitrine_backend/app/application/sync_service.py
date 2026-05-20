from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.interfaces.source import ProductSource
from app.core.models.product import Product
from app.domain.models.produto import Produto, ProdutoCodigo
from app.domain.models.cache_status import CacheStatus
from app.core.timer import temporizador
from app.core.error_handler import sanitizar_erro
import logging

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    produtos_count: int
    codigos_count: int


class SyncService:
    """Substitui o antigo ETL pipeline.

    Usa um ProductSource para obter a lista de produtos do ERP
    e sincroniza com o SQLite local (delete + insert).
    """

    def __init__(self, source: ProductSource, db: Session):
        self.source = source
        self.db = db

    def sync(self) -> SyncResult:
        logger.info("SyncService iniciando sync")

        with temporizador("SyncService completo", logger):
            products = self.source.get_all_products()
            logger.info("SyncService source retornou %s produtos", len(products))

            with temporizador("SyncService delete antigos", logger):
                self.db.execute(delete(ProdutoCodigo))
                self.db.execute(delete(Produto))

            produtos_orm = [self._to_orm(p) for p in products]

            with temporizador("SyncService insert", logger):
                self.db.add_all(produtos_orm)

            produtos_count = len(produtos_orm)
            codigos_count = sum(len(p.barcodes) for p in products)

            self.db.add(CacheStatus(
                last_updated=datetime.now(ZoneInfo("America/Sao_Paulo")),
                status="sucesso",
            ))

            self.db.commit()

            logger.info("SyncService concluido | produtos=%s codigos=%s", produtos_count, codigos_count)
            return SyncResult(produtos_count=produtos_count, codigos_count=codigos_count)

    def sync_com_erro(self, error: Exception) -> SyncResult:
        """Registra falha no sync sem alterar os dados."""
        logger.error("SyncService erro | %s", sanitizar_erro(error))
        self.db.add(CacheStatus(
            last_updated=datetime.now(ZoneInfo("America/Sao_Paulo")),
            status="erro",
            erro=sanitizar_erro(error),
        ))
        self.db.commit()
        raise RuntimeError("Erro ao sincronizar dados do ERP") from error

    @staticmethod
    def _to_orm(p: Product) -> Produto:
        return Produto(
            codigo_chamada=p.internal_code,
            nome=p.name,
            grupo=p.group,
            familia=p.family,
            preco_venda=float(p.sale_price),
            preco_custo=float(p.cost_price),
            estoque=p.stock,
            codigos=[
                ProdutoCodigo(codigo=b, codigo_chamada=p.internal_code)
                for b in p.barcodes
            ],
        )


def run_sync_scheduled():
    """Função para ser chamada pelo scheduler (sem argumentos).
    Cria seu próprio engine e sessão, executa o sync e invalida cache.
    """
    from app.infrastructure.db.bootstrap import init_db
    from app.infrastructure.db.session import SqliteSession
    from app.adapters.alterdata.product_source import AlterdataProductSource
    from app.adapters.alterdata.db import get_alterdata_engine
    from app.adapters.alterdata.transaction_source import invalidar_cache_transacoes

    init_db()
    session = SqliteSession()
    try:
        source = AlterdataProductSource(get_alterdata_engine(session))
        result = SyncService(source, session).sync()
        invalidar_cache_transacoes()
        logger.info("Sync agendado concluido | produtos=%s codigos=%s",
                     result.produtos_count, result.codigos_count)
    except Exception as e:
        logger.error("Sync agendado falhou: %s", sanitizar_erro(e))
    finally:
        session.close()
