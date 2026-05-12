from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ProdutoCodigoDTO:
    codigo: str
    codigo_chamada: str


@dataclass(frozen=True)
class ProdutoDTO:
    codigo_chamada: str
    nome: str
    grupo: str
    familia: str
    preco_venda: float
    preco_custo: float
    estoque: float
    codigos: List[ProdutoCodigoDTO]


@dataclass(frozen=True)
class ProdutoRow:
    codigo_chamada: str
    nome: str
    grupo: str
    familia: str
    preco_venda: float
    preco_custo: float
    estoque: float


@dataclass(frozen=True)
class CodigoRow:
    codigo: str
    codigo_chamada: str


@dataclass(frozen=True)
class ExtractResult:
    produtos: list[ProdutoRow]
    codigos: list[CodigoRow]