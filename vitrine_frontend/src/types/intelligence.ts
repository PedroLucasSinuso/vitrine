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
  // Macro contexto
  valor_indicador?: number | null
  variacao_ticket?: number | null
  variacao_faturamento?: number | null
  chave_indicador?: string | null
}

export type InsightTipo = 'encalhe' | 'margem_erosao' | 'taxa_troca' | 'oportunidade_b' | 'sazonalidade' | 'macro_contexto' | 'outro'
export type Impacto = 'alto' | 'medio' | 'baixo'
export type Confianca = 'alta' | 'media' | 'hipotese'
export type Fonte = 'claude' | 'gpt4o_mini' | 'deterministico'
export type IntelligenceStatus = 'idle' | 'loading' | 'ready' | 'error'

export interface ProdutoInsight {
  codigo: string
  nome: string
  grupo?: string | null
  estoque?: number | null
  dias_parado?: number | null
  ultima_venda?: string | null
  valor_estimado?: number | null
  taxa_troca?: number | null
  qtd_trocas?: number | null
  qtd_vendas?: number | null
  margem_anterior?: number | null
  margem_atual?: number | null
  variacao_pp?: number | null
  preco_medio_anterior?: number | null
  preco_medio_atual?: number | null
  crescimento_qtd?: number | null
  qtd_anterior?: number | null
  qtd_atual?: number | null
  valor_atual?: number | null
  receita?: number | null
  participacao?: number | null
  margem_b?: number | null
  margem_lider?: number | null
  upside_margem?: number | null
  potencial_ganho_mensal?: number | null
}

export interface Insight {
  hash: string
  tipo: InsightTipo
  impacto: Impacto
  confianca: Confianca
  titulo: string
  descricao: string
  sugestao: string
  metricas?: InsightMetricas | null
  produtos?: ProdutoInsight[] | null
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
