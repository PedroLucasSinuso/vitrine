import api from './client'
import type { Role } from '../types'

export interface Usuario {
  id: number
  username: string
  nome_exibicao: string
  role: Role
}

export interface UsuarioCreate {
  username: string
  nome_exibicao: string
  password: string
  role: Role
}

export interface UsuarioPatch {
  password?: string
  role?: Role
}

export async function listarUsuarios(): Promise<Usuario[]> {
  const response = await api.get('/auth/usuarios')
  return response.data
}

export async function criarUsuario(dados: UsuarioCreate): Promise<Usuario> {
  const response = await api.post('/auth/register', dados)
  return response.data
}

export async function atualizarUsuario(id: number, dados: UsuarioPatch): Promise<Usuario> {
  const response = await api.patch(`/auth/usuarios/${id}`, dados)
  return response.data
}

export async function excluirUsuario(id: number): Promise<void> {
  await api.delete(`/auth/usuarios/${id}`)
}