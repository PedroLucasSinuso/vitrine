export interface PeriodoEquipe {
  inicio: string
  fim: string
}

export interface IndicadoresVendedor {
  vendedor: string
  sem_vendedor: boolean
  faturamento_bruto: number
  trocas: number
  faturamento_liquido: number
  atendimentos: number
  pecas: number
  ticket_medio: number
  pa: number
  preco_medio_peca: number
  participacao: number
  variacao_liquido: number | null
  variacao_ticket_medio: number | null
  variacao_pa: number | null
  meta: number | null
  atingimento: number | null
  projecao: number | null
  comissao_estimada: number | null
}

export interface IndicadoresLoja {
  faturamento_bruto: number
  trocas: number
  faturamento_liquido: number
  atendimentos: number
  atendimentos_somados_por_vendedor: boolean
  ticket_medio: number
  pa: number
  meta: number | null
  atingimento: number | null
  projecao: number | null
}

export interface IndicadorIndisponivel {
  indicador: 'serie_diaria' | 'mix_categoria' | 'conversao_contatos'
  motivo: string
}

export interface ResultadoEquipe {
  periodo: PeriodoEquipe
  periodo_anterior: PeriodoEquipe | null
  competencia: string | null
  loja: IndicadoresLoja
  vendedores: IndicadoresVendedor[]
  indisponivel: IndicadorIndisponivel[]
}

export interface PontoSerieVendedor {
  data: string
  faturamento_bruto: number
  atendimentos: number
  pa: number
}

export interface ItemMixVendedor {
  grupo: string
  familia: string
  receita: number
  participacao: number
}

export interface MetaVendedor {
  vendedor: string
  valor_meta: number
  percentual_comissao: number
}

export interface MetasDaCompetencia {
  competencia: string
  metas: MetaVendedor[]
  vendedores_conhecidos: string[]
}

export interface AliasVendedor {
  nome_origem: string
  vendedor: string
}
