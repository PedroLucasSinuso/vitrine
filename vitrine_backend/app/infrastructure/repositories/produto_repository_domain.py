"""Repository que retorna ProdutoPuro (dataclass pura) em vez do model ORM.

Internamente usa o model SQLAlchemy ``Produto`` para fazer queries e
mapeia o resultado para ``ProdutoPuro``. Isso permite que serviços
de domínio operem sem conhecer SQLAlchemy, facilitando testes unitários
e desacoplando regras de negócio.

Este repositório convive com o ``ProdutoRepository`` antigo — ambos
podem ser usados simultaneamente durante a migração gradual.
"""

from typing import Optional
from sqlalchemy import select
from app.domain.models.produto import Produto, ProdutoCodigo
from app.domain.pure.produto_pure import ProdutoPuro
import logging

logger = logging.getLogger(__name__)


class ProdutoRepositoryDomain:
    """Repository orientado a domínio — retorna ``ProdutoPuro`` em vez de ORM.

    Aceita uma sessão SQLAlchemy (a mesma usada pelo resto do sistema).
    """

    def __init__(self, session) -> None:
        self._session = session

    # ── Métodos de consulta ─────────────────────────────────────────────

    def buscar_por_codigo(self, codigo: str) -> Optional[ProdutoPuro]:
        """Busca produto pelo código de chamada ou EAN/PLU.

        Retorna ``ProdutoPuro`` ou ``None`` se não encontrado.
        """
        logger.debug("DomainRepo buscar_por_codigo | codigo=%s", codigo)
        stmt = (
            select(Produto)
            .outerjoin(ProdutoCodigo)
            .where(
                (Produto.codigo_chamada == codigo) | (ProdutoCodigo.codigo == codigo)
            )
        )
        resultado = self._session.execute(stmt).scalars().first()
        if not resultado:
            logger.debug("DomainRepo buscar_por_codigo | nao encontrado | codigo=%s", codigo)
            return None
        logger.debug("DomainRepo buscar_por_codigo | encontrado | codigo=%s nome=%s", codigo, resultado.nome)
        return self._mapear(resultado)

    def buscar_por_nome(self, nome: str, limit: int = 20, offset: int = 0) -> list[ProdutoPuro]:
        """Busca produtos por nome (ILIKE).

        Retorna lista de ``ProdutoPuro``. Máximo 100 registros.
        """
        limit = max(1, min(limit, 100))
        logger.debug("DomainRepo buscar_por_nome | nome=%s limit=%s offset=%s", nome, limit, offset)
        stmt = (
            select(Produto)
            .where(Produto.nome.ilike(f"%{nome}%"))
            .offset(offset)
            .limit(limit)
        )
        resultados = self._session.execute(stmt).scalars().all()
        logger.debug("DomainRepo buscar_por_nome | rows=%s", len(resultados))
        return [self._mapear(r) for r in resultados]

    def listar_paginado(self, limit: int = 50, offset: int = 0) -> list[ProdutoPuro]:
        """Lista produtos com paginação."""
        limit = max(1, min(limit, 100))
        logger.debug("DomainRepo listar_paginado | limit=%s offset=%s", limit, offset)
        stmt = select(Produto).offset(offset).limit(limit)
        resultados = self._session.execute(stmt).scalars().all()
        return [self._mapear(r) for r in resultados]

    def listar_tabela(
        self,
        grupo: Optional[str] = None,
        familia: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "nome",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ProdutoPuro], int]:
        """Lista produtos com filtros, ordenação e paginação.

        Retorna (itens, total).
        """
        from sqlalchemy import func
        from app.infrastructure.repositories.produto_repository import _SORT_MAP

        stmt = select(Produto).where(Produto.ativo == True)
        count_stmt = select(func.count(Produto.codigo_chamada)).where(Produto.ativo == True)

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
        return [self._mapear(r) for r in items], total

    def obter_grupos_e_familias(self) -> tuple[list[str], list[str]]:
        """Retorna listas distintas de grupos e famílias de produtos ativos."""
        from sqlalchemy import select
        grupos = (
            self._session.execute(
                select(Produto.grupo).distinct().where(Produto.ativo == True).order_by(Produto.grupo)
            )
            .scalars()
            .all()
        )
        familias = (
            self._session.execute(
                select(Produto.familia).distinct().where(Produto.ativo == True).order_by(Produto.familia)
            )
            .scalars()
            .all()
        )
        return list(grupos), list(familias)

    # ── Métodos de escrita (sync) ───────────────────────────────────────

    def mapear_para_orm(self, puro: ProdutoPuro) -> Produto:
        """Converte ``ProdutoPuro`` de volta para o model ORM ``Produto``.

        Útil para persistência em operações de sync/ETL. O caller é
        responsável por adicionar/mergear a instância na sessão.
        """
        return Produto(
            codigo_chamada=puro.codigo_chamada,
            nome=puro.nome,
            grupo=puro.grupo,
            familia=puro.familia,
            preco_venda=puro.preco_venda,
            preco_custo=puro.preco_custo,
            estoque=puro.estoque,
            ativo=puro.ativo,
        )

    # ── Métodos auxiliares ─────────────────────────────────────────────

    @staticmethod
    def _mapear(orm: Produto) -> ProdutoPuro:
        """Converte model ORM ``Produto`` para ``ProdutoPuro``."""
        return ProdutoPuro(
            codigo_chamada=orm.codigo_chamada,
            nome=orm.nome,
            grupo=orm.grupo,
            familia=orm.familia,
            preco_venda=orm.preco_venda,
            preco_custo=orm.preco_custo,
            estoque=orm.estoque,
            ativo=orm.ativo,
            codigos=[c.codigo for c in orm.codigos] if orm.codigos else [],
        )
