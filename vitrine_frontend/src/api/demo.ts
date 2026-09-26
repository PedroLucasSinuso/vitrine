import api from './client'

export type PerfilDemo = 'supermercado' | 'moda' | 'equipe'

export async function perfisDemo(): Promise<PerfilDemo[]> {
  try {
    const response = await api.get<{ perfis: PerfilDemo[] }>('/auth/demo/perfis')
    return response.data.perfis
  } catch {
    return []
  }
}
