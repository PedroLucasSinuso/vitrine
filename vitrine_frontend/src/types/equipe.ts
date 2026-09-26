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
  novo?: boolean
  meta: number | null
  atingimento: number | null
  projecao: number | null
  comissao_estimada: number | null
  contatos?: number | null
  conversao?: number | null
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
  comparacao_parcial?: boolean
  competencia: string | null
  loja: IndicadoresLoja
  vendedores: IndicadoresVendedor[]
  indisponivel: IndicadorIndisponivel[]
  equipe?: ResumoEquipe | null
}

export interface ResumoEquipe {
  vendedores_ativos: number
  vendedores_ativos_anterior: number | null
  entradas: string[]
  saidas: string[]
  concentracao_top3: number | null
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

export interface ItemGrade {
  rotulo: string
  quantidade: number
  receita: number
  participacao: number
}

export interface ResultadoGrade {
  por_tamanho: ItemGrade[]
  por_cor: ItemGrade[]
  matriz: { tamanho: string; cor: string; quantidade: number }[]
  tamanhos: string[]
  cores: string[]
  grupos: string[]
  familias: string[]
  total_pecas: number
}

export interface PontoMensal {
  competencia: string
  inicio: string
  fim: string
  parcial: boolean
  sem_dados: boolean
  ausente: boolean
  faturamento_liquido: number | null
  atendimentos: number | null
  ticket_medio: number | null
  pa: number | null
  taxa_troca: number | null
  vendedores_ativos: number | null
}

export interface ComparacaoComLoja {
  ticket_medio: number | null
  pa: number | null
  preco_medio_peca: number | null
  taxa_troca: number | null
}

export interface DetalheVendedor {
  periodo: PeriodoEquipe
  periodo_anterior: PeriodoEquipe | null
  comparacao_parcial?: boolean
  indicadores: IndicadoresVendedor
  loja: IndicadoresLoja
  comparacao_loja: ComparacaoComLoja
  posicao: number | null
  total_vendedores: number
  serie_mensal: PontoMensal[] | null
  serie_diaria: PontoSerieVendedor[] | null
  mix: ItemMixVendedor[] | null
  indisponivel: IndicadorIndisponivel[]
}
