from collections.abc import Iterable
from dataclasses import dataclass

from app.domain.enums import ModoOperacao, Segmento

MODULOS_BI_BASE = frozenset({"dashboard", "receita", "ranking", "curva_abc", "trocas", "temporal", "sku"})
MODULOS_CATALOGO = frozenset({"busca", "produtos", "inventario", "etiquetas"})
MODULOS_QUE_EXIGEM_ERP = MODULOS_CATALOGO | {"perdas_consumo"}
MODULOS_QUE_EXIGEM_ITENS = MODULOS_BI_BASE | {"grade"}
MODULOS_DE_EQUIPE = frozenset({"equipe", "metas", "importacao"})
TIPO_ITENS = "itens_venda"


@dataclass(frozen=True)
class PerfilSegmento:
    modulos: frozenset[str]
    rotulos: dict[str, str]


def _rotulos(grupo: str, grupos: str, familia: str, familias: str, documento: str) -> dict[str, str]:
    return {"grupo": grupo, "grupos": grupos, "familia": familia, "familias": familias, "documento": documento}


PERFIS: dict[Segmento, PerfilSegmento] = {
    Segmento.SUPERMERCADO: PerfilSegmento(
        modulos=MODULOS_BI_BASE | {"perdas_consumo"} | MODULOS_CATALOGO,
        rotulos=_rotulos("Grupo", "Grupos", "Família", "Famílias", "Cupom"),
    ),
    Segmento.MODA: PerfilSegmento(
        modulos=MODULOS_BI_BASE | MODULOS_DE_EQUIPE | {"grade"} | MODULOS_CATALOGO,
        rotulos=_rotulos("Departamento", "Departamentos", "Categoria", "Categorias", "Atendimento"),
    ),
    Segmento.VAREJO: PerfilSegmento(
        modulos=MODULOS_BI_BASE | MODULOS_DE_EQUIPE | MODULOS_CATALOGO,
        rotulos=_rotulos("Departamento", "Departamentos", "Categoria", "Categorias", "Venda"),
    ),
    Segmento.EQUIPE: PerfilSegmento(
        modulos=MODULOS_DE_EQUIPE,
        rotulos=_rotulos("Departamento", "Departamentos", "Categoria", "Categorias", "Atendimento"),
    ),
}


def modulos_da_empresa(
    segmento: Segmento, modo: ModoOperacao, tipos_disponiveis: Iterable[str] = ()
) -> frozenset[str]:
    modulos = PERFIS[segmento].modulos
    if modo != ModoOperacao.UPLOAD:
        return modulos
    modulos = (modulos - MODULOS_QUE_EXIGEM_ERP) | {"importacao"}
    if TIPO_ITENS not in set(tipos_disponiveis):
        modulos = modulos - MODULOS_QUE_EXIGEM_ITENS
    return modulos


def rotulos_do_segmento(segmento: Segmento) -> dict[str, str]:
    return dict(PERFIS[segmento].rotulos)
