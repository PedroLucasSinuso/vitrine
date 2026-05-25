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
        try:
            return self._sync()
        except Exception as e:
            self.sync_com_erro(e)

    def _sync(self) -> SyncResult:
        logger.info("SyncService iniciando sync")

        with temporizador("SyncService completo", logger):
            # Fetch ALL products from ERP FIRST, THEN delete local data.
            # Isso elimina a janela de 0 produtos: se get_all_products()
            # falhar, o banco local permanece intacto.
            products = self.source.get_all_products()
            logger.info("SyncService source retornou %s produtos", len(products))

            # Transação explícita: DELETE + INSERT são atômicos.
            # Se add_all falhar, o rollback desfaz o DELETE.
            with self.db.begin():
                with temporizador("SyncService delete antigos", logger):
                    self.db.execute(delete(ProdutoCodigo))
                    self.db.execute(delete(Produto))

                produtos_orm = [self._to_orm(p) for p in products]

                with temporizador("SyncService insert", logger):
                    self.db.add_all(produtos_orm)

            # ── Gravar histórico de preços ──────────────────────────────────────
            with temporizador("SyncService historico_precos", logger):
                from app.infrastructure.repositories.produto_repository import ProdutoRepository
                from app.domain.models.sync_job import SyncJob
                repo = ProdutoRepository(self.db)
                ultimo_job = self.db.query(SyncJob).order_by(SyncJob.id.desc()).first()
                job_id = ultimo_job.id if ultimo_job else None

                for p in products:
                    repo.inserir_historico_preco(
                        codigo=p.internal_code,
                        preco_custo=float(p.cost_price),
                        preco_venda=float(p.sale_price),
                        sync_job_id=job_id,
                    )
                self.db.flush()

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
        self.db.rollback()  # limpa transação corrompida (ex: deletes parciais)
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
    O engine é disposto ao final para evitar vazamento de conexões PostgreSQL.
    """
    from app.infrastructure.db.bootstrap import init_db
    from app.infrastructure.db.session import SqliteSession
    from app.adapters.alterdata.product_source import AlterdataProductSource
    from app.adapters.alterdata.db import get_alterdata_engine
    from app.adapters.alterdata.transaction_source import invalidar_cache_transacoes

    init_db()
    session = SqliteSession()
    engine = None
    try:
        engine = get_alterdata_engine(session)
        source = AlterdataProductSource(engine)
        result = SyncService(source, session).sync()
        invalidar_cache_transacoes()
        logger.info("Sync agendado concluido | produtos=%s codigos=%s",
                     result.produtos_count, result.codigos_count)
    except Exception as e:
        logger.error("Sync agendado falhou: %s", sanitizar_erro(e))
    finally:
        session.close()
        if engine is not None:
            engine.dispose()
