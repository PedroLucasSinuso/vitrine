import api from './client'
import { getRole } from './auth'
import type { ProdutoBasico, ProdutoCompleto } from '../types'

export async function buscarProduto(codigo: string): Promise<ProdutoBasico | ProdutoCompleto> {
  const role = getRole()
  const endpoint = role === 'supervisor' || role === 'admin'
    ? `/produtos/${codigo}/completo`
    : `/produtos/${codigo}`

  const response = await api.get(endpoint)
  return response.data
}
export async function buscarProdutosPorNome(nome: string, limit = 20, offset = 0): Promise<ProdutoBasico[]> {
  const response = await api.get('/produtos/busca', { params: { nome, limit, offset } })
  return response.data
}

export async function registrarNaoEncontrado(codigo: string, observacao: string) {
  await api.post('/produtos/nao-encontrado', { codigo, observacao })
}