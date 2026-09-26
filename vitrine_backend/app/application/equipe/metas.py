import re
from decimal import Decimal

from sqlalchemy import delete, select, union
from sqlalchemy.orm import Session

from app.domain.models.importacao import (
    Dataset,
    DsContatoVendedor,
    DsItemVenda,
    DsVendaDiaria,
    DsVendaVendedorPeriodo,
)
from app.domain.models.metas import MetaVendedor, VendedorAlias
from vitrine_core.bi.equipe import Meta

COMPETENCIA = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class CompetenciaInvalida(ValueError):
    pass


def validar_competencia(competencia: str) -> str:
    if not COMPETENCIA.match(competencia):
        raise CompetenciaInvalida("Competência deve estar no formato AAAA-MM.")
    return competencia


def metas_da_competencia(db: Session, empresa_id: int, competencia: str) -> list[MetaVendedor]:
    return list(db.scalars(
        select(MetaVendedor)
        .where(MetaVendedor.empresa_id == empresa_id, MetaVendedor.competencia == competencia)
        .order_by(MetaVendedor.vendedor)
    ))


def metas_para_calculo(db: Session, empresa_id: int, competencia: str | None) -> dict[str, Meta]:
    if competencia is None:
        return {}
    return {
        m.vendedor: Meta(valor=m.valor_meta, percentual_comissao=m.percentual_comissao)
        for m in metas_da_competencia(db, empresa_id, competencia)
    }


def salvar_metas(db: Session, empresa_id: int, competencia: str, itens: list[dict], usuario_id: int | None) -> None:
    db.execute(delete(MetaVendedor).where(MetaVendedor.empresa_id == empresa_id, MetaVendedor.competencia == competencia))
    vistos = set()
    for item in itens:
        vendedor = item["vendedor"].strip()
        if not vendedor or vendedor.upper() in vistos:
            continue
        vistos.add(vendedor.upper())
        db.add(MetaVendedor(
            empresa_id=empresa_id, vendedor=vendedor, competencia=competencia,
            valor_meta=Decimal(str(item["valor_meta"])),
            percentual_comissao=Decimal(str(item.get("percentual_comissao") or 0)),
            atualizado_por=usuario_id,
        ))
    db.commit()


def copiar_metas(db: Session, empresa_id: int, destino: str, origem: str, usuario_id: int | None) -> int:
    itens = [
        {"vendedor": m.vendedor, "valor_meta": m.valor_meta, "percentual_comissao": m.percentual_comissao}
        for m in metas_da_competencia(db, empresa_id, origem)
    ]
    salvar_metas(db, empresa_id, destino, itens, usuario_id)
    return len(itens)


def aliases_da_empresa(db: Session, empresa_id: int) -> dict[str, str]:
    return {
        a.nome_origem: a.vendedor
        for a in db.scalars(select(VendedorAlias).where(VendedorAlias.empresa_id == empresa_id))
    }


def salvar_aliases(db: Session, empresa_id: int, aliases: dict[str, str]) -> None:
    db.execute(delete(VendedorAlias).where(VendedorAlias.empresa_id == empresa_id))
    for origem, destino in aliases.items():
        origem, destino = origem.strip(), destino.strip()
        if origem and destino and origem.upper() != destino.upper():
            db.add(VendedorAlias(empresa_id=empresa_id, nome_origem=origem, vendedor=destino))
    db.commit()


def vendedores_nos_dados(db: Session, empresa_id: int) -> list[str]:
    consultas = [
        select(modelo.vendedor.label("vendedor"))
        .join(Dataset, Dataset.id == modelo.dataset_id)
        .where(Dataset.empresa_id == empresa_id, modelo.vendedor.is_not(None))
        for modelo in (DsVendaVendedorPeriodo, DsVendaDiaria, DsItemVenda, DsContatoVendedor)
    ]
    nomes = {n.strip() for n in db.scalars(union(*consultas)) if n and n.strip()}
    return sorted(nomes, key=str.upper)
