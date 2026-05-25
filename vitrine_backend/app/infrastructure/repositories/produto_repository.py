from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from app.domain.models.historico_preco import HistoricoPreco
from app.domain.models.produto import Produto, ProdutoCodigo
from app.infrastructure.repositories.interfaces import IProdutoRepository
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)

_SORT_MAP = {
    "codigo_chamada": Produto.codigo_chamada,
    "nome": Produto.nome,
    "grupo": Produto.grupo,
    "familia": Produto.familia,
    "preco_venda": Produto.preco_venda,
    "preco_custo": Produto.preco_custo,
    "estoque": Produto.estoque,
}


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

    def listar_tabela(
        self,
        grupo: Optional[str] = None,
        familia: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "nome",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ):
        logger.debug(
            "Query listar_tabela | grupo=%s familia=%s search=%s sort=%s/%s limit=%s offset=%s",
            grupo, familia, search, sort_by, sort_order, limit, offset,
        )
        with temporizador("SQL listar_tabela", logger):
            stmt = select(Produto)
            count_stmt = select(func.count(Produto.codigo_chamada))

            if grupo:
                stmt = stmt.where(Produto.grupo == grupo)
                count_stmt = count_stmt.where(Produto.grupo == grupo)
            if familia:
                stmt = stmt.where(Produto.familia == familia)
                count_stmt = count_stmt.where(Produto.familia == familia)
            if search:
                filtro = f"%{search}%"
                stmt = stmt.where(
                    Produto.nome.ilike(filtro) | Produto.codigo_chamada.ilike(filtro)
                )
                count_stmt = count_stmt.where(
                    Produto.nome.ilike(filtro) | Produto.codigo_chamada.ilike(filtro)
                )

            order_col = _SORT_MAP.get(sort_by, Produto.nome)
            order_fn = order_col.desc() if sort_order == "desc" else order_col.asc()

            total = self._session.execute(count_stmt).scalar() or 0
            items = (
                self._session.execute(
                    stmt.order_by(order_fn).offset(offset).limit(limit)
                )
                .scalars()
                .all()
            )

        logger.info(
            "SQL listar_tabela | grupo=%s familia=%s search=%s total=%s rows=%s",
            grupo, familia, search, total, len(items),
        )
        return list(items), total

    def obter_grupos_e_familias(self):
        logger.debug("Query obter_grupos_e_familias")
        with temporizador("SQL obter_grupos_e_familias", logger):
            grupos = (
                self._session.execute(
                    select(Produto.grupo).distinct().order_by(Produto.grupo)
                )
                .scalars()
                .all()
            )
            familias = (
                self._session.execute(
                    select(Produto.familia).distinct().order_by(Produto.familia)
                )
                .scalars()
                .all()
            )
        logger.info(
            "SQL obter_grupos_e_familias | grupos=%s familias=%s",
            len(grupos), len(familias),
        )
        return list(grupos), list(familias)

    def inserir_historico_preco(
        self,
        codigo: str,
        preco_custo: float,
        preco_venda: float,
        sync_job_id: Optional[int] = None,
    ) -> None:
        logger.debug(
            "Query inserir_historico_preco | codigo=%s custo=%s venda=%s",
            codigo, preco_custo, preco_venda,
        )
        with temporizador("SQL inserir_historico_preco", logger):
            markup = (
                (preco_venda - preco_custo) / preco_custo if preco_custo else 0.0
            )
            margem = (
                (preco_venda - preco_custo) / preco_venda if preco_venda else 0.0
            )
            self._session.add(
                HistoricoPreco(
                    codigo_chamada=codigo,
                    preco_custo=preco_custo,
                    preco_venda=preco_venda,
                    markup=markup,
                    margem=margem,
                    data_coleta=datetime.now(ZoneInfo("America/Sao_Paulo")),
                    sync_job_id=sync_job_id,
                )
            )
        logger.info(
            "SQL inserir_historico_preco | codigo=%s markup=%.4f margem=%.4f",
            codigo, markup, margem,
        )