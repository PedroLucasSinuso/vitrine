from dataclasses import dataclass

from app.domain.enums import ModoOperacao, Segmento

MODULOS_BI_BASE = frozenset({"dashboard", "receita", "ranking", "curva_abc", "trocas", "temporal", "sku"})
MODULOS_CATALOGO = frozenset({"busca", "produtos", "inventario", "etiquetas"})
MODULOS_QUE_EXIGEM_ERP = MODULOS_CATALOGO | {"perdas_consumo"}


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
        modulos=MODULOS_BI_BASE | {"equipe", "metas", "grade", "importacao"} | MODULOS_CATALOGO,
        rotulos=_rotulos("Departamento", "Departamentos", "Categoria", "Categorias", "Atendimento"),
    ),
    Segmento.VAREJO: PerfilSegmento(
        modulos=MODULOS_BI_BASE | {"equipe", "metas", "importacao"} | MODULOS_CATALOGO,
        rotulos=_rotulos("Departamento", "Departamentos", "Categoria", "Categorias", "Venda"),
    ),
}


def modulos_da_empresa(segmento: Segmento, modo: ModoOperacao) -> frozenset[str]:
    modulos = PERFIS[segmento].modulos
    if modo == ModoOperacao.UPLOAD:
        return (modulos - MODULOS_QUE_EXIGEM_ERP) | {"importacao"}
    return modulos


def rotulos_do_segmento(segmento: Segmento) -> dict[str, str]:
    return dict(PERFIS[segmento].rotulos)
