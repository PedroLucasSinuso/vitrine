from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import delete, func
from sqlalchemy.orm import Session

from app.application.etl.dto import ProdutoDTO
from app.domain.models.produto import Produto, ProdutoCodigo
from app.domain.models.cache_status import CacheStatus
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)


def _to_orm(produto_dto: ProdutoDTO):
    return Produto(
        codigo_chamada=produto_dto.codigo_chamada,
        nome=produto_dto.nome,
        grupo=produto_dto.grupo,
        familia=produto_dto.familia,
        preco_custo=produto_dto.preco_custo,
        preco_venda=produto_dto.preco_venda,
        estoque=produto_dto.estoque,
        codigos=[
            ProdutoCodigo(
                codigo=c.codigo,
                codigo_chamada=c.codigo_chamada
            )
            for c in produto_dto.codigos
        ],
    )


def carregar_produtos(session: Session, produtos_dto: list[ProdutoDTO]) -> tuple[int, int]:
    with temporizador("ETL Load delete", logger):
        session.execute(delete(ProdutoCodigo))
        session.execute(delete(Produto))

    with temporizador("ETL Load orm", logger):
        produtos_orm = [_to_orm(p) for p in produtos_dto]

    with temporizador("ETL Load insert", logger):
        session.add_all(produtos_orm)

    produtos_count = len(produtos_orm)
    codigos_count = sum(len(p.codigos) for p in produtos_orm)

    logger.info("ETL Load | produtos=%s codigos=%s", produtos_count, codigos_count)
    return produtos_count, codigos_count


def atualizar_cache(session: Session, status: str = "sucesso", erro: str | None = None):
    session.add(CacheStatus(
        last_updated=datetime.now(ZoneInfo("America/Sao_Paulo")),
        status=status,
        erro=erro
    ))