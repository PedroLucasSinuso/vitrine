from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import delete, insert, select, update
from sqlalchemy.orm import Session

from vitrine_core.interfaces.source import ProductSource
from vitrine_core.models.product import Product
from app.domain.models.produto import Produto, ProdutoCodigo
from app.domain.models.cache_status import CacheStatus
from vitrine_core.timer import temporizador
from app.core.error_handler import sanitizar_erro
import logging

logger = logging.getLogger(__name__)

_LOTE = 500


@dataclass
class SyncResult:
    produtos_count: int
    codigos_count: int


class SyncService:
    """Substitui o antigo ETL pipeline.

    Usa um ProductSource para obter a lista de produtos do ERP
    e sincroniza com o banco local — escopado a UMA
    empresa: cada tenant tem seu próprio ERP, então o sync de uma empresa
    nunca deve tocar os produtos de outra (ver histórico: antes desta
    versão, o DELETE aqui não tinha filtro nenhum e apagava produtos/
    códigos de TODAS as empresas a cada sync de qualquer uma).
    """

    def __init__(self, source: ProductSource, db: Session, empresa_id: int):
        self.source = source
        self.db = db
        self.empresa_id = empresa_id

    def sync(self, job_id: str | None = None) -> SyncResult:
        try:
            return self._sync(job_id=job_id)
        except Exception as e:
            self.sync_com_erro(e)

    def _sync(self, job_id: str | None = None) -> SyncResult:
        logger.info("SyncService iniciando sync | empresa_id=%s", self.empresa_id)

        with temporizador("SyncService completo", logger):
            # Fetch ALL products from ERP FIRST, THEN delete local data.
            # Isso elimina a janela de 0 produtos: se get_all_products()
            # falhar, o banco local permanece intacto.
            products = self.source.get_all_products()
            logger.info("SyncService source retornou %s produtos", len(products))

            with temporizador("SyncService catalogo", logger):
                self._aplicar_catalogo(products)

            # ── Gravar histórico de preços (dentro da transação atômica — C1)
            with temporizador("SyncService historico_precos", logger):
                from app.infrastructure.repositories.produto_repository import ProdutoRepository

                from app.domain.models.sync_job import SyncJob

                if job_id is None:
                    ultimo_job = (
                        self.db.query(SyncJob)
                        .filter(SyncJob.empresa_id == self.empresa_id)
                        .order_by(SyncJob.id.desc())
                        .first()
                    )
                    job_id_resolved = ultimo_job.id if ultimo_job else None
                else:
                    job_id_resolved = self.db.scalar(
                        select(SyncJob.id).where(
                            SyncJob.job_id == job_id, SyncJob.empresa_id == self.empresa_id
                        )
                    )

                repo = ProdutoRepository(self.db, empresa_id=self.empresa_id)
                for p in products:
                    repo.inserir_historico_preco(
                        codigo=p.internal_code,
                        preco_custo=float(p.cost_price),
                        preco_venda=float(p.sale_price),
                        sync_job_id=job_id_resolved,
                    )

            # ── CacheStatus dentro da transação ─────────────────────────────
            self.db.add(CacheStatus(
                empresa_id=self.empresa_id,
                last_updated=datetime.now(ZoneInfo("America/Sao_Paulo")),
                status="sucesso",
            ))

            self.db.commit()

            produtos_count = len(products)
            codigos_count = sum(len(p.barcodes) for p in products)

            logger.info(
                "SyncService concluido | empresa_id=%s produtos=%s codigos=%s",
                self.empresa_id, produtos_count, codigos_count,
            )
            return SyncResult(produtos_count=produtos_count, codigos_count=codigos_count)

    def sync_com_erro(self, error: Exception) -> SyncResult:
        """Registra falha no sync sem alterar os dados."""
        self.db.rollback()  # limpa transação corrompida (ex: deletes parciais)
        logger.error("SyncService erro | empresa_id=%s | %s", self.empresa_id, sanitizar_erro(error))
        self.db.add(CacheStatus(
            empresa_id=self.empresa_id,
            last_updated=datetime.now(ZoneInfo("America/Sao_Paulo")),
            status="erro",
            erro=sanitizar_erro(error),
        ))
        self.db.commit()
        raise RuntimeError("Erro ao sincronizar dados do ERP") from error

    def _aplicar_catalogo(self, products: list[Product]) -> None:
        existentes = set(self.db.scalars(
            select(Produto.codigo_chamada).where(Produto.empresa_id == self.empresa_id)
        ))
        novos = {p.internal_code for p in products}

        self.db.execute(
            delete(ProdutoCodigo).where(ProdutoCodigo.empresa_id == self.empresa_id)
        )
        removidos = sorted(existentes - novos)
        for inicio in range(0, len(removidos), _LOTE):
            self.db.execute(
                delete(Produto).where(
                    Produto.empresa_id == self.empresa_id,
                    Produto.codigo_chamada.in_(removidos[inicio:inicio + _LOTE]),
                )
            )

        linhas = [self._linha_produto(p) for p in products]
        atualizar = [linha for linha in linhas if linha["codigo_chamada"] in existentes]
        inserir = [linha for linha in linhas if linha["codigo_chamada"] not in existentes]
        if atualizar:
            self.db.execute(update(Produto), atualizar)
        if inserir:
            self.db.execute(insert(Produto), inserir)

        codigos = [
            {"empresa_id": self.empresa_id, "codigo": b, "codigo_chamada": p.internal_code}
            for p in products
            for b in p.barcodes
        ]
        if codigos:
            self.db.execute(insert(ProdutoCodigo), codigos)

    def _linha_produto(self, p: Product) -> dict:
        return {
            "empresa_id": self.empresa_id,
            "codigo_chamada": p.internal_code,
            "nome": p.name,
            "grupo": p.group,
            "familia": p.family,
            "preco_venda": float(p.sale_price),
            "preco_custo": float(p.cost_price),
            "estoque": p.stock,
            "ativo": p.is_active,
        }


def run_sync_scheduled(empresa_id: int | None = None):
    """Função para ser chamada pelo scheduler.

    Com ``empresa_id``, sincroniza só aquela empresa — é assim que o
    scheduler por-tenant (um job "etl_sync_{empresa_id}" por empresa, ver
    app/application/scheduler_manager.py) chama isso. Sem ``empresa_id``
    (uso manual/fallback), sincroniza TODAS as empresas ativas, cada uma
    isoladamente — uma falha no ERP de uma empresa não impede a
    sincronização das demais.
    """
    from app.infrastructure.db.bootstrap import init_db
    from app.infrastructure.db.session import SessionLocal
    from app.application.erp_factory import run_sync_common
    from app.domain.enums import ModoOperacao
    from app.domain.models.empresa import Empresa

    init_db()
    session = SessionLocal()
    try:
        if empresa_id is not None:
            alvos = [empresa_id]
        else:
            alvos = [
                e.id for e in
                session.query(Empresa)
                .filter(Empresa.status == "ativa", Empresa.modo != ModoOperacao.UPLOAD.value)
                .all()
            ]
        for eid in alvos:
            try:
                result = run_sync_common(session, empresa_id=eid, pool_size=1)
                logger.info(
                    "Sync agendado concluido | empresa_id=%s produtos=%s codigos=%s",
                    eid, result.produtos_count, result.codigos_count,
                )
            except Exception as e:
                logger.error(
                    "Sync agendado falhou | empresa_id=%s erro=%s", eid, sanitizar_erro(e)
                )
    finally:
        session.close()
