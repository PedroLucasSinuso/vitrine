export type TipoDataset =
  | 'vendas_vendedor_periodo' | 'vendas_diarias' | 'vendas_produto_periodo' | 'contatos_vendedor' | 'itens_venda'

export type StatusImportacao = 'aguardando_mapeamento' | 'pronto' | 'divergente' | 'confirmado' | 'erro'

export type Celula = string | number | null

export interface ColunaMapeada {
  indice: number
  campo: string
}

export interface Mapeamento {
  tipo: TipoDataset
  linha_cabecalho: number
  colunas: ColunaMapeada[]
  ignorar_linhas_com?: string[]
  formato_data: 'dd/mm/aaaa' | 'aaaa-mm-dd' | 'mm/dd/aaaa'
  separador_decimal: ',' | '.'
  periodo?: { inicio: string; fim: string } | null
}

export interface Previa {
  registros: Record<string, Celula>[]
  total_registros: number
  descartadas: { indice: number; motivo: string }[]
  total_descartadas: number
  periodo: { inicio: string; fim: string } | null
  erros: string[]
  validacao: {
    status: 'conferido' | 'divergente' | 'sem_total'
    campos_conferidos: string[]
    diferencas: { campo: string; calculado: number; informado: number }[]
  }
  confirmavel: boolean
}

export interface Importacao {
  id: number
  nome: string
  formato: string
  status: StatusImportacao
  criado_em: string
  template_aplicado: boolean
  duplicado_de: number | null
  grade: Celula[][]
  total_linhas: number
  mapeamento: Mapeamento | null
  previa: Previa | null
  sugestao_ia?: { confianca: 'alta' | 'media' | 'baixa' | null; duvidas: string[]; erro: string | null } | null
}

export interface ImportacaoResumo {
  id: number
  nome: string
  formato: string
  status: StatusImportacao
  criado_em: string
}

export interface CampoDataset {
  campo: string
  rotulo: string
  tipo: 'texto' | 'numero' | 'inteiro' | 'data' | 'operacao'
  obrigatorio: boolean
}

export interface DatasetResumo {
  id: number
  tipo: TipoDataset
  inicio: string
  fim: string
  linhas: number
  nome_origem: string
  criado_em: string
}
