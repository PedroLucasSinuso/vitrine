export interface ProdutoBasico {
  codigo_chamada: string
  codigo_buscado: string | null
  nome: string
  preco_venda: number
  estoque: number
  grupo: string
  familia: string
}

export interface ProdutoCompleto extends ProdutoBasico {
  preco_custo: number
  markup: number
  margem: number
}
