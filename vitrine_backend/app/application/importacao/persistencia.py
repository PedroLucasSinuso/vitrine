from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.importacao import (
    Dataset,
    DsContatoVendedor,
    DsItemVenda,
    DsVendaDiaria,
    DsVendaProdutoPeriodo,
    DsVendaVendedorPeriodo,
)
from vitrine_core.datasets.tipos import (
    ContatoVendedor,
    ItemVenda,
    Operacao,
    TipoDataset,
    VendaDiaria,
    VendaProdutoPeriodo,
    VendaVendedorPeriodo,
)


ZERO = Decimal("0")

MODELO_POR_TIPO = {
    TipoDataset.VENDAS_VENDEDOR_PERIODO: DsVendaVendedorPeriodo,
    TipoDataset.VENDAS_DIARIAS: DsVendaDiaria,
    TipoDataset.VENDAS_PRODUTO_PERIODO: DsVendaProdutoPeriodo,
    TipoDataset.CONTATOS_VENDEDOR: DsContatoVendedor,
    TipoDataset.ITENS_VENDA: DsItemVenda,
}


def _linha(tipo: TipoDataset, registro: dict) -> dict:
    if tipo == TipoDataset.VENDAS_VENDEDOR_PERIODO:
        return {
            "vendedor": registro["vendedor"], "atendimentos": registro["atendimentos"],
            "pecas": registro.get("pecas") or ZERO, "faturamento_bruto": registro["faturamento_bruto"],
            "trocas": registro.get("trocas") or ZERO, "faturamento_liquido": registro.get("faturamento_liquido"),
        }
    if tipo == TipoDataset.VENDAS_DIARIAS:
        return {
            "data": registro["data"], "vendedor": registro.get("vendedor"),
            "faturamento_bruto": registro["faturamento_bruto"], "trocas": registro.get("trocas") or ZERO,
            "atendimentos": registro.get("atendimentos") or 0, "pecas": registro.get("pecas") or ZERO,
        }
    if tipo == TipoDataset.VENDAS_PRODUTO_PERIODO:
        return {
            "produto": registro["produto"], "codigo_produto": registro.get("codigo_produto"),
            "grupo": registro.get("grupo") or "", "familia": registro.get("familia") or "",
            "quantidade": registro["quantidade"], "receita": registro["receita"], "custo": registro.get("custo"),
        }
    if tipo == TipoDataset.CONTATOS_VENDEDOR:
        return {
            "vendedor": registro["vendedor"], "contatos": registro["contatos"],
            "respostas": registro.get("respostas"), "conversoes": registro.get("conversoes"),
        }
    operacao = registro.get("operacao") or Operacao.VENDA
    return {
        "documento": registro["documento"], "data": registro["data"], "operacao": Operacao(operacao).value,
        "quantidade": abs(registro["quantidade"]), "valor": abs(registro["valor"]),
        "produto": registro.get("produto") or "", "codigo_produto": registro.get("codigo_produto"),
        "grupo": registro.get("grupo") or "", "familia": registro.get("familia") or "",
        "vendedor": registro.get("vendedor"), "tamanho": registro.get("tamanho") or "",
        "cor": registro.get("cor") or "", "colecao": registro.get("colecao") or "",
        "hora": registro.get("hora"),
    }


def gravar_dataset(
    db: Session,
    empresa_id: int,
    tipo: TipoDataset,
    periodo: tuple[date, date],
    registros: list[dict],
    nome_origem: str,
    arquivo_id: int | None = None,
    template_id: int | None = None,
) -> Dataset:
    dataset = Dataset(
        empresa_id=empresa_id, tipo=tipo.value, inicio=periodo[0], fim=periodo[1],
        linhas=len(registros), arquivo_id=arquivo_id, nome_origem=nome_origem, template_id=template_id,
    )
    db.add(dataset)
    db.flush()
    modelo = MODELO_POR_TIPO[tipo]
    db.add_all(modelo(dataset_id=dataset.id, **_linha(tipo, r)) for r in registros)
    return dataset


def datasets_da_empresa(db: Session, empresa_id: int, tipo: TipoDataset | None = None) -> list[Dataset]:
    consulta = select(Dataset).where(Dataset.empresa_id == empresa_id)
    if tipo is not None:
        consulta = consulta.where(Dataset.tipo == tipo.value)
    return list(db.scalars(consulta.order_by(Dataset.criado_em.desc(), Dataset.id.desc())))


def _para_dominio(tipo: TipoDataset, dataset: Dataset, linha):
    if tipo == TipoDataset.VENDAS_VENDEDOR_PERIODO:
        return VendaVendedorPeriodo(
            inicio=dataset.inicio, fim=dataset.fim, vendedor=linha.vendedor, atendimentos=linha.atendimentos,
            pecas=linha.pecas, faturamento_bruto=linha.faturamento_bruto, trocas=linha.trocas,
            faturamento_liquido=linha.faturamento_liquido,
        )
    if tipo == TipoDataset.VENDAS_DIARIAS:
        return VendaDiaria(
            data=linha.data, vendedor=linha.vendedor, faturamento_bruto=linha.faturamento_bruto,
            trocas=linha.trocas, atendimentos=linha.atendimentos, pecas=linha.pecas,
        )
    if tipo == TipoDataset.VENDAS_PRODUTO_PERIODO:
        return VendaProdutoPeriodo(
            inicio=dataset.inicio, fim=dataset.fim, produto=linha.produto, codigo_produto=linha.codigo_produto,
            grupo=linha.grupo, familia=linha.familia, quantidade=linha.quantidade, receita=linha.receita,
            custo=linha.custo,
        )
    if tipo == TipoDataset.CONTATOS_VENDEDOR:
        return ContatoVendedor(
            inicio=dataset.inicio, fim=dataset.fim, vendedor=linha.vendedor, contatos=linha.contatos,
            respostas=linha.respostas, conversoes=linha.conversoes,
        )
    return ItemVenda(
        documento=linha.documento, data=linha.data, operacao=Operacao(linha.operacao),
        quantidade=linha.quantidade, valor=linha.valor, produto=linha.produto,
        codigo_produto=linha.codigo_produto, grupo=linha.grupo, familia=linha.familia,
        vendedor=linha.vendedor, tamanho=linha.tamanho, cor=linha.cor, colecao=linha.colecao,
        hora=linha.hora,
    )


def linhas_do_dataset(db: Session, dataset: Dataset) -> list:
    tipo = TipoDataset(dataset.tipo)
    modelo = MODELO_POR_TIPO[tipo]
    linhas = db.scalars(select(modelo).where(modelo.dataset_id == dataset.id).order_by(modelo.id))
    return [_para_dominio(tipo, dataset, linha) for linha in linhas]


def excluir_dataset(db: Session, dataset: Dataset) -> None:
    from sqlalchemy import delete

    modelo = MODELO_POR_TIPO[TipoDataset(dataset.tipo)]
    db.execute(delete(modelo).where(modelo.dataset_id == dataset.id))
    db.delete(dataset)
