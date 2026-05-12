export type Dimensao = 'produto' | 'grupo' | 'familia'
export type Metrica = 'receita_produto' | 'qtd_item'
export type CurvaAbc = 'A' | 'B' | 'C'

export interface KpisDTO {
  faturamento_bruto: number
  faturamento_liquido: number
  total_trocas: number
  qtd_tickets: number
  ticket_medio: number
  itens_por_ticket: number
}

export interface VariacaoKpi {
  atual: number
  anterior: number | null
  variacao_pct: number | null
}

export interface KpisComparativoDTO {
  faturamento_bruto: VariacaoKpi
  faturamento_liquido: VariacaoKpi
  total_trocas: VariacaoKpi
  qtd_tickets: VariacaoKpi
  ticket_medio: VariacaoKpi
  itens_por_ticket: VariacaoKpi
  dados_parciais_ate: string | null
}

export interface ItemDimensaoDTO {
  grupo: string
  familia?: string | null
  produto?: string | null
  valor: number
}

export interface ItemCurvaAbcDTO {
  grupo: string
  familia?: string | null
  produto?: string | null
  receita: number
  participacao_pct: number
  participacao_acumulada: number
  curva: CurvaAbc
}

export interface ItemRankingDTO {
  codigo: string
  produto: string
  valor: number
}

export interface ItemMovimentoDTO {
  codigo: string
  produto: string
  receita: number
}

export interface TrocasDTO {
  total_trocas: number
  taxa_troca_pct: number
  por_produto: ItemMovimentoDTO[]
}

export interface MovimentoDTO {
  total: number
  por_produto: ItemMovimentoDTO[]
}

export interface PontoDiarioDTO {
  data: string
  valor: number
}

export interface PontoHoraDTO {
  hora: string
  valor: number
}

export interface PontoDiaSemanaDTO {
  dia_semana: string
  valor: number
}

export interface SkuDTO {
  codigo: string
  produto: string
  grupo: string
  familia: string
  receita_total: number
  qtd_total: number
  qtd_tickets: number
  ticket_medio: number
  ranking_dias: PontoDiarioDTO[]
  distribuicao_hora: PontoHoraDTO[]
}

export interface PeriodoBi {
  data_inicio: string
  data_fim: string
}