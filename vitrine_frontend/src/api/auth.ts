import api from './client'
import type { AuthToken } from '../types'

export async function login(username: string, password: string): Promise<AuthToken> {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)

  const response = await api.post<AuthToken>('/auth/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}