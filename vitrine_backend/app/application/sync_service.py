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
from app.application.normalizacao_service import normalizar
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

    def sync(self, job_id: str | None = None) -> SyncResult:
        try:
            return self._sync(job_id=job_id)
        except Exception as e:
            self.sync_com_erro(e)

    def _sync(self, job_id: str | None = None) -> SyncResult:
        logger.info("SyncService iniciando sync")

        with temporizador("SyncService completo", logger):
            # 1. Fetch ALL products from ERP FIRST, THEN convert to ORM.
            #    Nenhuma escrita no banco até que tudo esteja pronto em memória.
            products = self.source.get_all_products()
            logger.info("SyncService source retornou %s produtos", len(products))

            # 2. Converte para ORM FIRST, DEPOIS deleta + insere.
            #    Sem with self.db.begin(): montar_url_postgres() já ativou
            #    autobegin na session (via query de config). begin()
            #    explícito causaria "A transaction is already begun on
            #    this Session" — o erro clássico do 1º clique.
            produtos_orm = [self._to_orm(p, self.db) for p in products]

            with temporizador("SyncService delete antigos", logger):
                self.db.execute(delete(ProdutoCodigo))
                self.db.execute(delete(Produto))

            with temporizador("SyncService insert", logger):
                self.db.add_all(produtos_orm)

            # 4. Histórico de preços (após transação principal, pode ser atômico separado)
            with temporizador("SyncService historico_precos", logger):
                from app.infrastructure.repositories.produto_repository import ProdutoRepository

                if job_id is None:
                    from app.domain.models.sync_job import SyncJob
                    ultimo_job = self.db.query(SyncJob).order_by(SyncJob.id.desc()).first()
                    job_id_resolved = ultimo_job.id if ultimo_job else None
                else:
                    job_id_resolved = job_id

                repo = ProdutoRepository(self.db)
                for p in products:
                    repo.inserir_historico_preco(
                        codigo=p.internal_code,
                        preco_custo=float(p.cost_price),
                        preco_venda=float(p.sale_price),
                        sync_job_id=job_id_resolved,
                    )

            # 5. CacheStatus
            self.db.add(CacheStatus(
                last_updated=datetime.now(ZoneInfo("America/Sao_Paulo")),
                status="sucesso",
            ))
            self.db.commit()

            produtos_count = len(produtos_orm)
            codigos_count = sum(len(p.barcodes) for p in products)

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
    def _to_orm(p: Product, db: Session) -> Produto:
        grupo_norm, familia_norm = normalizar(db, p.group, p.family)
        return Produto(
            codigo_chamada=p.internal_code,
            nome=p.name,
            grupo=grupo_norm,
            familia=familia_norm,
            preco_venda=float(p.sale_price),
            preco_custo=float(p.cost_price),
            estoque=p.stock,
            ativo=p.is_active,
            codigos=[
                ProdutoCodigo(codigo=b, codigo_chamada=p.internal_code)
                for b in p.barcodes
            ],
        )


def run_sync_scheduled():
    """Função para ser chamada pelo scheduler (sem argumentos).
    Cria sua própria sessão, executa o sync via run_sync_common, invalida cache
    e dispara triggers pós-sync (margem negativa, erro).
    """
    from app.infrastructure.db.bootstrap import init_db
    from app.infrastructure.db.session import SqliteSession
    from app.application.erp_factory import run_sync_common
    from app.application.triggers_pos_sync import (
        verificar_margem_negativa,
        verificar_erro_sync,
    )

    init_db()
    session = SqliteSession()
    try:
        result = run_sync_common(session, pool_size=1)
        logger.info("Sync agendado concluido | produtos=%s codigos=%s",
                     result.produtos_count, result.codigos_count)

        # Triggers pós-sync bem-sucedido
        verificar_margem_negativa(session)
        verificar_erro_sync(session)  # resolve notificações de erro
    except Exception as e:
        erro_msg = sanitizar_erro(e)
        logger.error("Sync agendado falhou: %s", erro_msg)
        # Trigger de notificação de erro (só se houver sessão válida)
        try:
            verificar_erro_sync(session, erro=erro_msg)
        except Exception:
            logger.warning("Falha ao criar notificação de erro", exc_info=True)
    finally:
        session.close()
