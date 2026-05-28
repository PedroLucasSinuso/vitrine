/** Hook para o módulo Intelligence — polling, cache sessionStorage, dismiss. */
import { useCallback, useRef, useState } from 'react'
import { fetchIntelligence, fetchIntelligenceStatus, dismissInsightAPI } from '../api/intelligence'
import type { IntelligenceResponse } from '../types/intelligence'

type IntelligenceStatus = 'idle' | 'loading' | 'ready' | 'error'
type IntelligenceError = { message: string } | null

const SESSION_STORAGE_KEY = 'vitrine_intelligence'
const POLLING_INTERVAL = 2000
const POLLING_TIMEOUT = 300_000 // 5 min

function setCache(data: IntelligenceResponse) {
  try {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify({ data, timestamp: Date.now() }))
  } catch {
    // sessionStorage cheio ou indisponível — ignora
  }
}

export function useIntelligence() {
  const [status, setStatus] = useState<IntelligenceStatus>('idle')
  const [resultado, setResultado] = useState<IntelligenceResponse | null>(null)
  const [erro, setErro] = useState<IntelligenceError>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const controllerRef = useRef<AbortController | null>(null)

  const pararPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  const gerarAnalise = useCallback(async () => {
    // Aborta requisição anterior se houver
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller
    const signal = controller.signal

    // Remove cache sessionStorage para forçar requisição ao backend
    sessionStorage.removeItem(SESSION_STORAGE_KEY)

    setStatus('loading')
    setResultado(null)
    setErro(null)
    setJobId(null)

    try {
      const data = await fetchIntelligence(signal)

      if ('job_id' in data && data.job_id) {
        // 2. Cache miss — inicia polling
        setJobId(data.job_id)
        const jobIdVal = data.job_id
        const inicio = Date.now()

        pararPolling()
        pollingRef.current = setInterval(async () => {
          try {
            const pollSignal = controller.signal
            const jobStatus = await fetchIntelligenceStatus(jobIdVal, pollSignal)

            if (jobStatus.status === 'ready' && jobStatus.resultado) {
              pararPolling()
              setResultado(jobStatus.resultado)
              setStatus('ready')
              setCache(jobStatus.resultado)
            } else if (jobStatus.status === 'error') {
              pararPolling()
              setErro({ message: jobStatus.erro || 'Análise falhou no processamento' })
              setStatus('error')
            } else if (Date.now() - inicio > POLLING_TIMEOUT) {
              pararPolling()
              setErro({ message: 'A análise excedeu o tempo limite. Tente novamente.' })
              setStatus('error')
            }
          } catch {
            // polling continua na próxima iteração
          }
        }, POLLING_INTERVAL)
      } else {
        // 3. Cache hit ou fallback — resposta já veio
        const response = data as IntelligenceResponse
        setResultado(response)
        setStatus('ready')
        setCache(response)
      }
    } catch (e: unknown) {
      const err = e as { name?: string; message?: string; response?: { status?: number; data?: { error?: string } } }
      if (err?.name === 'CanceledError' || err?.name === 'AbortError') return
      const errorMsg = err?.response?.data?.error || err?.message || 'Erro desconhecido'
      console.error('[Intelligence] fetchIntelligence failed:', err?.response?.status, errorMsg)
      setErro({ message: errorMsg })
      setStatus('error')
    }
  }, [pararPolling])

  const dismissInsight = useCallback(async (hash: string) => {
    try {
      await dismissInsightAPI(hash)
      // Remove do estado local
      setResultado(prev => prev ? {
        ...prev,
        insights: prev.insights.filter(i => i.hash !== hash),
      } : prev)
    } catch {
      // silencioso — falha no dismiss não bloqueia UX
    }
  }, [])

  return { status, resultado, erro, jobId, gerarAnalise, dismissInsight }
}
