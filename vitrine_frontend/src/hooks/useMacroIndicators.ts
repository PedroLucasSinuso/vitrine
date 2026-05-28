/** Hook para buscar indicadores macroeconômicos do endpoint /bi/intelligence/macro. */
import { useEffect, useRef, useState } from 'react'
import api from '../api/client'
import type { MacroIndicator } from '../types/macro'

type MacroStatus = 'loading' | 'ready' | 'error'

interface UseMacroReturn {
  indicadores: MacroIndicator[]
  status: MacroStatus
  erro: string | null
}

export function useMacroIndicators(): UseMacroReturn {
  const [indicadores, setIndicadores] = useState<MacroIndicator[]>([])
  const [status, setStatus] = useState<MacroStatus>('loading')
  const [erro, setErro] = useState<string | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    setStatus('loading')

    api.get('/bi/intelligence/macro')
      .then(res => {
        if (!mountedRef.current) return
        const data = res.data as MacroIndicator[]
        setIndicadores(data)
        setStatus('ready')
      })
      .catch((e: unknown) => {
        if (!mountedRef.current) return
        const err = e as { message?: string; response?: { data?: { error?: string } } }
        const msg = err?.response?.data?.error || err?.message || 'Erro ao carregar indicadores'
        setErro(msg)
        setStatus('error')
      })

    return () => { mountedRef.current = false }
  }, [])

  return { indicadores, status, erro }
}
