from pydantic import BaseModel
from typing import Literal

class KpisDTO(BaseModel):
    faturamento_bruto: float
    faturamento_liquido: float
    total_trocas: float
    qtd_tickets: int
    ticket_medio: float
    itens_por_ticket: float

class VariacaoKpi(BaseModel):
    atual: float
    anterior: float | None = None
    variacao_pct: float | None = None

class KpisComparativoDTO(BaseModel):
    faturamento_bruto: VariacaoKpi
    faturamento_liquido: VariacaoKpi
    total_trocas: VariacaoKpi
    qtd_tickets: VariacaoKpi
    ticket_medio: VariacaoKpi
    itens_por_ticket: VariacaoKpi
    dados_parciais_ate: str | None = None

class ItemDimensaoDTO(BaseModel):
    codigo: str = ""
    grupo: str
    familia: str | None = None
    produto: str | None = None
    valor: float

class ItemCurvaAbcDTO(BaseModel):
    codigo: str = ""
    grupo: str
    familia: str | None = None
    produto: str | None = None
    receita: float
    participacao_pct: float
    participacao_acumulada: float
    curva: Literal["A", "B", "C"]

class ItemRankingDTO(BaseModel):
    codigo: str
    produto: str
    valor: float

class ItemMovimentoDTO(BaseModel):
    codigo: str
    produto: str
    receita: float

class TrocasDTO(BaseModel):
    total_trocas: float
    taxa_troca_pct: float
    por_produto: list[ItemMovimentoDTO]

class MovimentoDTO(BaseModel):
    total: float
    por_produto: list[ItemMovimentoDTO]

class PontoDiarioDTO(BaseModel):
    data: str
    valor: float

class PontoHoraDTO(BaseModel):
    hora: str
    valor: float

class PontoDiaSemanaDTO(BaseModel):
    dia_semana: str
    valor: float

class SkuDTO(BaseModel):
    codigo: str
    produto: str
    grupo: str
    familia: str
    receita_total: float
    qtd_total: float
    qtd_tickets: int
    ticket_medio: float
    ranking_dias: list[PontoDiarioDTO]
    distribuicao_hora: list[PontoHoraDTO]