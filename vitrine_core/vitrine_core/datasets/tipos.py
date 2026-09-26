from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from enum import Enum


class TipoDataset(str, Enum):
    ITENS_VENDA = "itens_venda"
    VENDAS_DIARIAS = "vendas_diarias"
    VENDAS_VENDEDOR_PERIODO = "vendas_vendedor_periodo"
    VENDAS_PRODUTO_PERIODO = "vendas_produto_periodo"
    CONTATOS_VENDEDOR = "contatos_vendedor"


class Operacao(str, Enum):
    VENDA = "venda"
    TROCA = "troca"


@dataclass(frozen=True)
class ItemVenda:
    documento: str
    data: date
    operacao: Operacao
    quantidade: Decimal
    valor: Decimal
    produto: str = ""
    codigo_produto: str | None = None
    grupo: str = ""
    familia: str = ""
    vendedor: str | None = None
    tamanho: str = ""
    cor: str = ""
    colecao: str = ""
    hora: time | None = None


@dataclass(frozen=True)
class VendaDiaria:
    data: date
    faturamento_bruto: Decimal
    atendimentos: int
    pecas: Decimal
    trocas: Decimal = Decimal("0")
    vendedor: str | None = None


@dataclass(frozen=True)
class VendaVendedorPeriodo:
    inicio: date
    fim: date
    vendedor: str | None
    atendimentos: int
    pecas: Decimal
    faturamento_bruto: Decimal
    trocas: Decimal = Decimal("0")
    faturamento_liquido: Decimal | None = None


@dataclass(frozen=True)
class VendaProdutoPeriodo:
    inicio: date
    fim: date
    produto: str
    quantidade: Decimal
    receita: Decimal
    codigo_produto: str | None = None
    grupo: str = ""
    familia: str = ""
    custo: Decimal | None = None


@dataclass(frozen=True)
class ContatoVendedor:
    inicio: date
    fim: date
    vendedor: str | None
    contatos: int
    respostas: int | None = None
    conversoes: int | None = None
