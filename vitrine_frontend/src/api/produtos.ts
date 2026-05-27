import { jwtDecode } from 'jwt-decode'
import api from './client'
import { getAccessToken } from './tokenStore'
import type { ProdutoBasico, ProdutoCompleto, Role } from '../types'

function _getRole(): Role | null {
  const token = getAccessToken()
  if (!token) return null
  try {
    return jwtDecode<{ role?: Role }>(token).role ?? null
  } catch {
    return null
  }
}

export async function buscarProduto(codigo: string): Promise<ProdutoBasico | ProdutoCompleto> {
  const role = _getRole()
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

export async function reportarNaoEncontrado(codigo: string, observacao: string): Promise<void> {
  await api.post('/produtos/nao-encontrado', { codigo, observacao })
}