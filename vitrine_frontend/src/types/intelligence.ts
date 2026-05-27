/** Tipos para o módulo Vitrine Intelligence (análise semanal com IA). */

export interface InsightMetricas {
  // Encalhe
  total_encalhados?: number | null
  valor_total_encalhado?: number | null
  // Erosão de margem
  margem_anterior?: number | null
  margem_atual?: number | null
  variacao?: number | null
  // Taxa de troca
  taxa?: number | null
  qtd_trocas?: number | null
  qtd_vendas?: number | null
  // Oportunidade B
  margem_b?: number | null
  margem_lider?: number | null
  potencial_ganho_mensal?: number | null
  // Sugestão de preço promocional
  preco_atual?: number | null
  preco_sugerido?: number | null
  economia_percentual?: number | null
}

export type InsightTipo = 'encalhe' | 'margem_erosao' | 'taxa_troca' | 'oportunidade_b' | 'sazonalidade' | 'outro'
export type Impacto = 'alto' | 'medio' | 'baixo'
export type Confianca = 'alta' | 'media' | 'hipotese'
export type Fonte = 'claude' | 'gpt4o_mini' | 'deterministico'
export type IntelligenceStatus = 'idle' | 'loading' | 'ready' | 'error'

export interface Insight {
  hash: string
  tipo: InsightTipo
  impacto: Impacto
  confianca: Confianca
  titulo: string
  descricao: string
  sugestao: string
  metricas?: InsightMetricas | null
}

export interface IntelligenceResponse {
  resumo_executivo: string
  insights: Insight[]
  fonte: Fonte
  gerado_em: string
}

export interface IntelligenceJobStatus {
  job_id: string
  status: string
  resultado?: IntelligenceResponse | null
  erro?: string | null
}
