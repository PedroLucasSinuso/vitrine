/** Hook para o módulo Intelligence — polling, cache sessionStorage, dismiss. */
import { useCallback, useRef, useState } from 'react'
import { fetchIntelligence, fetchIntelligenceStatus, dismissInsightAPI } from '../api/intelligence'
import type { IntelligenceResponse, IntelligenceStatus } from '../types/intelligence'

const SESSION_STORAGE_KEY = 'vitrine_intelligence'
const POLLING_INTERVAL = 2000
const POLLING_TIMEOUT = 300_000 // 5 min
const CACHE_TTL = 3_600_000 // 1h (sessionStorage)

function getCache(): { data: IntelligenceResponse; timestamp: number } | null {
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
    return null
  }
}

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

    // 1. Verifica cache
    const cached = getCache()
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      setResultado(cached.data)
      setStatus('ready')
      return
    }

    setStatus('loading')
    setResultado(null)
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
              setStatus('error')
            } else if (Date.now() - inicio > POLLING_TIMEOUT) {
              pararPolling()
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
      const err = e as { name?: string }
      if (err?.name === 'CanceledError' || err?.name === 'AbortError') return
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

  return { status, resultado, jobId, gerarAnalise, dismissInsight }
}
