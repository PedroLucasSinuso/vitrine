export interface SessaoInventario {
  id: number
  nome: string
  status: string
  codigo_convite: string
  criado_por: string
  criado_em: string
  total_operadores: number
  total_itens: number
}

export interface ItemInventario {
  codigo: string
  nome: string
  grupo: string
  familia: string
  quantidade: number
}

export interface ItemInventarioSubmit {
  codigo: string
  nome: string
  grupo: string
  familia: string
  quantidade?: number
}
