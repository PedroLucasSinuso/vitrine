"""Pydantic schemas for Vitrine Intelligence API responses."""
from datetime import datetime
from pydantic import BaseModel
from typing import Literal


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
    # Sugestão de preço promocional
    preco_atual: float | None = None
    preco_sugerido: float | None = None
    economia_percentual: float | None = None


class Insight(BaseModel):
    hash: str
    tipo: Literal["encalhe", "margem_erosao", "taxa_troca", "oportunidade_b", "sazonalidade", "outro"]
    impacto: Literal["alto", "medio", "baixo"]
    confianca: Literal["alta", "media", "hipotese"] = "alta"
    titulo: str
    descricao: str
    sugestao: str
    metricas: InsightMetricas | None = None


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
