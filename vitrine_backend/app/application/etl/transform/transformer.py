from collections import defaultdict
from typing import Dict, Iterable, List, Set

from app.application.etl.dto import (
    ProdutoCodigoDTO,
    ProdutoDTO,
    ProdutoRow,
    CodigoRow,
)
from app.core.timer import temporizador
import logging

logger = logging.getLogger(__name__)


def transformar_produtos(
    produtos_rows: Iterable[ProdutoRow],
    codigos_rows: Iterable[CodigoRow],
) -> List[ProdutoDTO]:
    with temporizador("ETL Transform", logger):
        produtos_list = list(produtos_rows)
        codigos_por_produto = _agrupar_codigos_por_produto(codigos_rows)
        resultado = [
            _criar_produto_dto(produto_row, codigos_por_produto)
            for produto_row in produtos_list
        ]
    logger.info("ETL Transform | input_rows=%s output=%s", len(produtos_list), len(resultado))
    return resultado


def _agrupar_codigos_por_produto(
    codigos_rows: Iterable[CodigoRow],
) -> Dict[str, Set[str]]:
    agrupados: Dict[str, Set[str]] = defaultdict(set)

    for row in codigos_rows:
        if not row.codigo:
            continue

        agrupados[row.codigo_chamada].add(row.codigo)

    return agrupados


def _criar_produto_dto(
    row: ProdutoRow,
    codigos_por_produto: Dict[str, Set[str]],
) -> ProdutoDTO:
    codigos = codigos_por_produto.get(row.codigo_chamada, set())

    return ProdutoDTO(
        codigo_chamada=row.codigo_chamada,
        nome=row.nome,
        grupo=row.grupo,
        familia=row.familia,
        preco_custo=row.preco_custo,
        preco_venda=row.preco_venda,
        estoque=row.estoque,
        codigos=_criar_codigos_dto(row.codigo_chamada, codigos),
    )


def _criar_codigos_dto(
    codigo_chamada: str,
    codigos: Iterable[str],
) -> List[ProdutoCodigoDTO]:
    return [
        ProdutoCodigoDTO(
            codigo=codigo,
            codigo_chamada=codigo_chamada,
        )
        for codigo in codigos
    ]