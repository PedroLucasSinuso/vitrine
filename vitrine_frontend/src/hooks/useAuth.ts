import { useCallback } from 'react'
import { jwtDecode } from 'jwt-decode'
import api from '../api/client'
import { login as apiLogin } from '../api/auth'
import { getAccessToken, setAccessToken } from '../api/tokenStore'
import type { JwtPayload, Role } from '../types'

function getToken(): string | null {
  return getAccessToken()
}

function parseJwtPayload(token: string): JwtPayload | null {
  try {
    return jwtDecode<JwtPayload>(token)
  } catch {
    return null
  }
}

function isTokenExpired(token: string): boolean {
  const payload = parseJwtPayload(token)
  if (!payload) return true

  const exp = (payload as JwtPayload & { exp?: number }).exp
  if (!exp) return false

  const now = Date.now() / 1000
  return exp < now
}

function _getTokenExp(token: string): number | null {
  const payload = parseJwtPayload(token)
  if (!payload) return null
  return (payload as JwtPayload & { exp?: number }).exp ?? null
}

function _getExpiresInMs(token: string): number {
  const exp = _getTokenExp(token)
  if (exp === null) return 0
  const remaining = exp * 1000 - Date.now()
  return Math.max(0, remaining)
}

export function useAuth() {
  const isAuthenticated = useCallback((): boolean => {
    const token = getToken()
    if (!token) return false
    if (isTokenExpired(token)) {
      return false
    }
    return true
  }, [])

  const getRole = useCallback((): Role | null => {
    const token = getToken()
    if (!token || isTokenExpired(token)) return null

    const payload = parseJwtPayload(token)
    return payload?.role ?? null
  }, [])

  const getUsername = useCallback((): string | null => {
    const token = getToken()
    if (!token) return null
    const payload = parseJwtPayload(token)
    return payload?.sub ?? null
  }, [])

  const getNomeExibicao = useCallback((): string => {
    const token = getToken()
    if (!token) return ''
    const payload = parseJwtPayload(token)
    if (!payload) return ''
    return `${payload.nome_exibicao ?? payload.sub} (${payload.role})`
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const data = await apiLogin(username, password)
    const decoded = jwtDecode<JwtPayload>(data.access_token)
    setAccessToken(data.access_token)
    return decoded.role as Role
  }, [])

  const logout = useCallback(async () => {
    let revoked = false
    try {
      await api.post('/auth/logout', {}, { timeout: 10000 })
      revoked = true
    } catch (err) {
      console.warn(
        '[Auth] Não foi possível revogar o token no servidor.',
        err
      )
    }
    setAccessToken(null)
    if (!revoked) {
      console.warn('[Auth] Token pode ainda ser válido.')
    }
  }, [])

  const checkAuth = useCallback(() => {
    const valid = isAuthenticated()
    return valid
  }, [isAuthenticated])

  const getTokenExp = useCallback((): number | null => {
    const token = getToken()
    if (!token) return null
    return _getTokenExp(token)
  }, [])

  const getExpiresInMs = useCallback((): number => {
    const token = getToken()
    if (!token) return 0
    return _getExpiresInMs(token)
  }, [])

  return { isAuthenticated, getRole, getUsername, getNomeExibicao, login, logout, checkAuth, getTokenExp, getExpiresInMs }
}
