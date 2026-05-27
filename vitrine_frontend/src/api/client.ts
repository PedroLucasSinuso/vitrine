import axios from 'axios'
import { getAccessToken, setAccessToken } from './tokenStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  withCredentials: true,  // cookies HttpOnly (cross-tab/production)
})

// Flag para evitar loop infinito de refresh
let _isRefreshing = false
let _refreshSubscribers: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

function _onRefreshed(newToken: string) {
  _refreshSubscribers.forEach((s) => s.resolve(newToken))
  _refreshSubscribers = []
}

function _onRefreshFailed(error: unknown) {
  _refreshSubscribers.forEach((s) => s.reject(error))
  _refreshSubscribers = []
}

function _addRefreshSubscriber(resolve: (token: string) => void, reject: (err: unknown) => void) {
  _refreshSubscribers.push({ resolve, reject })
}

async function _tryRefreshToken(): Promise<string | null> {
  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_URL ?? '/api'}/auth/refresh`,
      {},
      {
        headers: { 'Content-Type': 'application/json' },
        withCredentials: true,
      },
    )
    const { access_token } = response.data
    if (access_token) setAccessToken(access_token)
    return access_token
  } catch {
    return null
  }
}

// CSRF token — read from cookie
function getCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : null
}

// Interceptor: Authorization header from in-memory token + CSRF on mutations
api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (config.method && !['get', 'head', 'options'].includes(config.method)) {
    const csrfToken = getCsrfToken()
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      if (_isRefreshing) {
        return new Promise((resolve, reject) => {
          _addRefreshSubscriber(
            (newToken: string) => {
              originalRequest.headers.Authorization = `Bearer ${newToken}`
              resolve(api(originalRequest))
            },
            (err) => reject(err),
          )
        })
      }

      originalRequest._retry = true
      _isRefreshing = true

      const newToken = await _tryRefreshToken()
      _isRefreshing = false

      if (newToken) {
        _onRefreshed(newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      }

      // Rejeita subscribers pendentes em vez de apenas limpar (evita memory leak)
      _onRefreshFailed(error)
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }

    return Promise.reject(error)
  }
)

/**
 * Tenta renovar o token proativamente no startup da aplicação.
 * Útil quando a página é recarregada e o cookie HttpOnly ainda é válido
 * mas o token em memória foi perdido. Chamar cedo evita 401s em cascata.
 */
export async function tryRefreshOnStartup(): Promise<boolean> {
  if (getAccessToken()) return true
  const token = await _tryRefreshToken()
  return token !== null
}

export default api
