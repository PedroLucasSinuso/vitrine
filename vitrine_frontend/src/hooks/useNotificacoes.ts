import { useState, useEffect, useCallback, useRef } from 'react'
import type { Notificacao } from '../types/notificacao'
import { fetchNotificacoes, fetchNaoLidas, marcarComoLida, marcarTodasComoLidas } from '../api/notificacoes'

const POLL_INTERVAL = 30_000 // 30s

export function useNotificacoes() {
  const [notificacoes, setNotificacoes] = useState<Notificacao[]>([])
  const [naoLidas, setNaoLidas] = useState(0)
  const [loading, setLoading] = useState(true)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const carregar = useCallback(async () => {
    try {
      const [lista, count] = await Promise.all([
        fetchNotificacoes(),
        fetchNaoLidas(),
      ])
      setNotificacoes(lista.notificacoes)
      setNaoLidas(count.count)
    } catch {
      // Silencioso — não quebrar a UI por causa de notificações
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    carregar()
    intervalRef.current = setInterval(carregar, POLL_INTERVAL)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [carregar])

  const ler = useCallback(async (id: number) => {
    await marcarComoLida(id)
    setNotificacoes((prev) =>
      prev.map((n) => (n.id === id ? { ...n, lida: true } : n)),
    )
    setNaoLidas((prev) => Math.max(0, prev - 1))
  }, [])

  const lerTodas = useCallback(async () => {
    await marcarTodasComoLidas()
    setNotificacoes((prev) => prev.map((n) => (n.lida ? n : { ...n, lida: true })))
    setNaoLidas(0)
  }, [])

  const recarregar = useCallback(() => {
    setLoading(true)
    carregar()
  }, [carregar])

  return {
    notificacoes,
    naoLidas,
    loading,
    ler,
    lerTodas,
    recarregar,
  }
}
