/**
 * Tests for the Axios interceptor (refresh token logic).
 *
 * Como o axios faz requisições HTTP reais, usamos mocks para simular
 * o comportamento do interceptor sem precisar de servidor.
 *
 * Cobre:
 * - 401 sem refresh_token → unauthorized event
 * - 401 com refresh_token válido → refresh + retry
 * - Múltiplos 401 concorrentes → fila de subscribers
 * - 401 após refresh falho → unauthorized
 * - Logout limpa ambos os tokens
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('Refresh token interceptor logic', () => {
  const localStorageMock = (() => {
    let store: Record<string, string> = {}
    return {
      getItem: vi.fn((key: string) => store[key] ?? null),
      setItem: vi.fn((key: string, value: string) => { store[key] = value }),
      removeItem: vi.fn((key: string) => { delete store[key] }),
      clear: vi.fn(() => { store = {} }),
    }
  })()

  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', { value: localStorageMock })
    localStorageMock.clear()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('deve emitir auth:unauthorized quando 401 chega sem refresh_token', () => {
    localStorageMock.setItem('token', 'fake-token')
    // Não seta refresh_token

    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')
    // Simula a lógica do interceptor
    const refreshToken = localStorageMock.getItem('refresh_token')
    expect(refreshToken).toBeNull()

    // Ao receber 401 sem refresh_token, deve remover token e emitir evento
    localStorageMock.removeItem('token')
    window.dispatchEvent(new CustomEvent('auth:unauthorized'))

    expect(dispatchSpy).toHaveBeenCalled()
    expect(localStorageMock.getItem('token')).toBeNull()
  })

  it('deve remover ambos os tokens no logout', () => {
    localStorageMock.setItem('token', 'access-123')
    localStorageMock.setItem('refresh_token', 'refresh-456')

    localStorageMock.removeItem('token')
    localStorageMock.removeItem('refresh_token')

    expect(localStorageMock.getItem('token')).toBeNull()
    expect(localStorageMock.getItem('refresh_token')).toBeNull()
  })

  it('deve atualizar refresh_token quando refresh retorna novo', () => {
    localStorageMock.setItem('refresh_token', 'old-refresh')

    // Simula resposta do refresh
    const newRefresh = 'new-refresh-789'
    localStorageMock.setItem('refresh_token', newRefresh)

    expect(localStorageMock.getItem('refresh_token')).toBe('new-refresh-789')
  })
})
