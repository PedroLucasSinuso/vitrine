import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
})

// Flag para evitar loop infinito de refresh
let _isRefreshing = false
let _refreshSubscribers: ((token: string) => void)[] = []

function _onRefreshed(newToken: string) {
  _refreshSubscribers.forEach((cb) => cb(newToken))
  _refreshSubscribers = []
}

function _addRefreshSubscriber(cb: (token: string) => void) {
  _refreshSubscribers.push(cb)
}

async function _tryRefreshToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) return null

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_URL ?? '/api'}/auth/refresh`,
      { refresh_token: refreshToken },
      { headers: { 'Content-Type': 'application/json' } },
    )
    const { access_token, refresh_token: newRefresh } = response.data
    localStorage.setItem('token', access_token)
    if (newRefresh) {
      localStorage.setItem('refresh_token', newRefresh)
    }
    return access_token
  } catch {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    return null
  }
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Só tenta refresh em 401 e se não for a própria chamada de refresh
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      if (_isRefreshing) {
        // Outra requisição já está tentando refresh — aguarda
        return new Promise((resolve) => {
          _addRefreshSubscriber((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            resolve(api(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      _isRefreshing = true

      const newToken = await _tryRefreshToken()
      _isRefreshing = false

      if (newToken) {
        // Notifica subscribers e re-tenta a requisição original
        _onRefreshed(newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      }

      // Refresh falhou — emite unauthorized
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      _refreshSubscribers = []
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }

    return Promise.reject(error)
  }
)

export default api
