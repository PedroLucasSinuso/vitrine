from typing import Optional
from sqlalchemy import select
from app.infrastructure.repositories.interfaces import IProdutoRepository
from app.domain.models.produto import Produto, ProdutoCodigo
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)


class ProdutoRepository(IProdutoRepository):
    def __init__(self, session) -> None:
        self._session = session

    def listar_paginado(self, limit: int = 50, offset: int = 0):
        logger.debug("Query listar_paginado | limit=%s offset=%s", limit, offset)
        with temporizador("SQL listar_paginado", logger):
            stmt = select(Produto).offset(offset).limit(limit)
            resultado = self._session.execute(stmt).scalars().all()
        logger.info("SQL listar_paginado | limit=%s offset=%s rows=%s", limit, offset, len(resultado))
        return resultado

    def obter_por_codigo(self, codigo: str) -> Optional[Produto]:
        logger.debug("Query obter_por_codigo | codigo=%s", codigo)
        with temporizador("SQL obter_por_codigo", logger):
            stmt = (
                select(Produto)
                .join(ProdutoCodigo)
                .where(ProdutoCodigo.codigo == codigo)
            )
            resultado = self._session.execute(stmt).scalars().first()
        logger.info("SQL obter_por_codigo | codigo=%s encontrado=%s", codigo, resultado is not None)
        return resultado

    def buscar_por_nome(self, nome: str, limit: int = 20, offset: int = 0):
        logger.debug("Query buscar_por_nome | nome=%s limit=%s offset=%s", nome, limit, offset)
        with temporizador("SQL buscar_por_nome", logger):
            stmt = (
                select(Produto)
                .where(Produto.nome.ilike(f"%{nome}%"))
                .offset(offset)
                .limit(limit)
            )
            resultado = self._session.execute(stmt).scalars().all()
        logger.info("SQL buscar_por_nome | nome=%s rows=%s", nome, len(resultado))
        return resultado