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

export async function logout(navigate: (path: string) => void) {
  try {
    await api.post('/auth/logout')
  } catch {
    // Falha silenciosa — melhor limpar localStorage de qualquer forma
  }
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  navigate('/login')
}

export function getRole(): Role | null {
  return localStorage.getItem('role') as Role | null
}