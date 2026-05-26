"""Serviço de domínio para Produto — opera com ``ProdutoPuro``.

Usa o ``ProdutoRepositoryDomain`` que retorna dataclasses puras,
permitindo que regras de negócio sejam testadas sem banco de dados.

Este serviço convive com o ``ProdutoService`` antigo (que retorna
ORM). A migração da API routes para este serviço é opcional e gradual.
"""

from typing import Optional
from app.infrastructure.repositories.produto_repository_domain import ProdutoRepositoryDomain
from app.domain.pure.produto_pure import ProdutoPuro
import logging

logger = logging.getLogger(__name__)
logger_nao_encontrado = logging.getLogger("app.nao_encontrado")


class ProdutoServiceDomain:
    """Serviço orientado a domínio — retorna ``ProdutoPuro``."""

    def __init__(self, repo: ProdutoRepositoryDomain) -> None:
        self.repo = repo

    def listar_paginado(self, limit: int = 50, offset: int = 0) -> list[ProdutoPuro]:
        """Lista produtos com paginação."""
        limit = max(1, min(limit, 100))
        return self.repo.listar_paginado(limit, offset)

    def obter_por_codigo(self, codigo: str) -> Optional[ProdutoPuro]:
        """Busca produto por código."""
        produto = self.repo.buscar_por_codigo(codigo)
        if not produto:
            logger.warning("Produto não encontrado (domain) | codigo=%s", codigo)
            logger_nao_encontrado.info(
                "Produto não encontrado | codigo=%s | origem=service_domain", codigo
            )
        return produto

    def buscar_por_nome(self, nome: str, limit: int = 20, offset: int = 0) -> list[ProdutoPuro]:
        """Busca produtos por nome."""
        nome = nome.strip()
        if len(nome) < 2:
            return []
        limit = max(1, min(limit, 100))
        return self.repo.buscar_por_nome(nome, limit, offset)

    def get_all_products(self) -> list[ProdutoPuro]:
        """Retorna todos os produtos cadastrados (sem paginação)."""
        return self.repo.listar_paginado(limit=999999, offset=0)
