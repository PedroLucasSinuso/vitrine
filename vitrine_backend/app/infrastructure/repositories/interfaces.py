from typing import Optional
from abc import ABC, abstractmethod
from app.domain.models.produto import Produto


class IProdutoRepository(ABC):
    @abstractmethod
    def listar_paginado(self, limit: int, offset: int) -> list[Produto]:
        pass

    @abstractmethod
    def obter_por_codigo(self, codigo: str) -> Optional[Produto]:
        pass

    @abstractmethod
    def buscar_por_nome(self, nome: str, limit: int, offset: int) -> list[Produto]:
        pass

    @abstractmethod
    def listar_tabela(
        self,
        grupo: Optional[str] = None,
        familia: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "nome",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Produto], int]:
        pass

    @abstractmethod
    def obter_grupos_e_familias(self) -> tuple[list[str], list[str]]:
        pass

    @abstractmethod
    def inserir_historico_preco(
        self,
        codigo: str,
        preco_custo: float,
        preco_venda: float,
        sync_job_id: Optional[int] = None,
    ) -> None:
        pass