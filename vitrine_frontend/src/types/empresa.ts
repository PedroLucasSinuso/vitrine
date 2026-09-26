export type Segmento = 'supermercado' | 'moda' | 'varejo'
export type ModoOperacao = 'legado' | 'upload' | 'agente'

export type Modulo =
  | 'dashboard' | 'receita' | 'ranking' | 'curva_abc' | 'trocas' | 'perdas_consumo'
  | 'temporal' | 'sku' | 'busca' | 'produtos' | 'inventario' | 'etiquetas'
  | 'equipe' | 'metas' | 'grade'

export type ChaveRotulo = 'grupo' | 'grupos' | 'familia' | 'familias' | 'documento'

export interface PerfilEmpresa {
  nome: string
  segmento: Segmento
  modo: ModoOperacao
  modulos: Modulo[]
  rotulos: Record<ChaveRotulo, string>
}
