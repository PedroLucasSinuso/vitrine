import api from './client'
import type { PerfilEmpresa } from '../types'

export async function getPerfilEmpresa(): Promise<PerfilEmpresa> {
  const response = await api.get<PerfilEmpresa>('/empresa/perfil')
  return response.data
}
