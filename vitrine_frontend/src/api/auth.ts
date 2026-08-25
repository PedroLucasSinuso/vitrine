import { jwtDecode } from 'jwt-decode'
import api from './client'
import type { AuthToken, Role } from '../types'

export async function login(username: string, password: string): Promise<AuthToken> {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)

  const response = await api.post<AuthToken>('/auth/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}

/** Se este servidor tem modo de demonstração provisionado. */
export async function demoDisponivel(): Promise<boolean> {
  try {
    const response = await api.get<{ disponivel: boolean }>('/auth/demo')
    return response.data.disponivel
  } catch {
    // Numa instalação de cliente real a rota pode nem existir; sem demo
    // a landing simplesmente não oferece o botão.
    return false
  }
}

/** Entra na demonstração sem credencial (botão "Ver demo" da landing). */
export async function entrarNaDemo(): Promise<AuthToken> {
  const response = await api.post<AuthToken>('/auth/demo')
  return response.data
}

export function getRole(): Role | null {
  const token = localStorage.getItem('token')
  if (!token) return null
  try {
    const decoded = jwtDecode<{ role?: Role }>(token)
    return decoded.role ?? null
  } catch {
    return null
  }
}