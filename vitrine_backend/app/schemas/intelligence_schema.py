"""Pydantic schemas for Vitrine Intelligence API responses."""
from datetime import datetime
from pydantic import BaseModel
from typing import Literal


class ProdutoInsight(BaseModel):
    """Produto listado no detalhamento de um insight."""
    codigo: str
    nome: str
    grupo: str | None = None
    estoque: float | None = None
    dias_parado: int | None = None
    ultima_venda: str | None = None
    valor_estimado: float | None = None
    # Taxa de troca
    taxa_troca: float | None = None
    qtd_trocas: int | None = None
    qtd_vendas: int | None = None
    # Erosão de margem
    margem_anterior: float | None = None
    margem_atual: float | None = None
    variacao_pp: float | None = None
    preco_medio_anterior: float | None = None
    preco_medio_atual: float | None = None
    # Sazonalidade
    crescimento_qtd: float | None = None
    qtd_anterior: int | None = None
    qtd_atual: int | None = None
    valor_atual: float | None = None
    # Oportunidade B
    receita: float | None = None
    participacao: float | None = None
    margem_b: float | None = None
    margem_lider: float | None = None
    upside_margem: float | None = None
    potencial_ganho_mensal: float | None = None


class InsightMetricas(BaseModel):
    """Métricas específicas por tipo de insight."""
    # Encalhe
    total_encalhados: int | None = None
    valor_total_encalhado: float | None = None
    # Erosão de margem
    margem_anterior: float | None = None
    margem_atual: float | None = None
    variacao: float | None = None
    # Taxa de troca
    taxa: float | None = None
    qtd_trocas: int | None = None
    qtd_vendas: int | None = None
    # Oportunidade B
    margem_b: float | None = None
    margem_lider: float | None = None
    potencial_ganho_mensal: float | None = None
    # Macro contexto
    valor_indicador: float | None = None
    variacao_ticket: float | None = None
    variacao_faturamento: float | None = None
    chave_indicador: str | None = None
    # Sugestão de preço promocional
    preco_atual: float | None = None
    preco_sugerido: float | None = None
    economia_percentual: float | None = None


class Insight(BaseModel):
    hash: str
    tipo: Literal["encalhe", "margem_erosao", "taxa_troca", "oportunidade_b", "sazonalidade", "macro_contexto", "outro"]
    impacto: Literal["alto", "medio", "baixo"]
    confianca: Literal["alta", "media", "hipotese"] = "alta"
    titulo: str
    descricao: str
    sugestao: str
    metricas: InsightMetricas | None = None
    produtos: list[ProdutoInsight] | None = None


class IntelligenceResponse(BaseModel):
    """Resposta completa da análise do Intelligence."""
    resumo_executivo: str
    insights: list[Insight]
    fonte: Literal["claude", "gpt4o_mini", "deterministico"]
    gerado_em: datetime


class IntelligenceJobStatus(BaseModel):
    """Status de job para polling."""
    job_id: str
    status: str  # "processing" | "ready" | "error"
    resultado: IntelligenceResponse | None = None
    erro: str | None = None
