from typing import List, Optional
from app.infrastructure.repositories.interfaces import IProdutoRepository
from app.domain.models.produto import Produto
import logging

logger = logging.getLogger(__name__)
logger_nao_encontrado = logging.getLogger("app.nao_encontrado")


class ProdutoService:
    def __init__(self, repo: IProdutoRepository):
        self.repo = repo

    def listar_paginado(self, limit: int = 50, offset: int = 0) -> List[Produto]:
        limit = max(1, min(limit, 100))
        return self.repo.listar_paginado(limit, offset)

    def obter_por_codigo(self, codigo: str) -> Optional[Produto]:
        produto = self.repo.obter_por_codigo(codigo)

        if not produto:
            logger.warning("Produto não encontrado | codigo=%s", codigo)
            logger_nao_encontrado.info("Produto não encontrado | codigo=%s | origem=service", codigo)

        return produto

    def buscar_por_nome(self, nome: str, limit: int = 20, offset: int = 0) -> List[Produto]:
        nome = nome.strip()
        if len(nome) < 2:
            return []
        limit = max(1, min(limit, 100))
        return self.repo.buscar_por_nome(nome, limit, offset)