/** API functions for Vitrine Intelligence module. */
import api from './client'
import type { IntelligenceResponse, IntelligenceJobStatus } from '../types/intelligence'

/**
 * Solicita análise. Retorna o response se cache hit, ou { status, job_id } se criou job.
 */
export async function fetchIntelligence(signal?: AbortSignal): Promise<IntelligenceResponse | { status: string; job_id: string }> {
  const hoje = new Date()
  const trintaDiasAtras = new Date(hoje)
  trintaDiasAtras.setDate(trintaDiasAtras.getDate() - 30)
  const params = {
    data_inicio: trintaDiasAtras.toISOString().split('T')[0],
    data_fim: hoje.toISOString().split('T')[0],
  }
  const r = await api.get('/bi/intelligence', { params, signal })
  return r.data
}

/**
 * Polling de status do job.
 */
export async function fetchIntelligenceStatus(
  jobId: string,
  data_inicio: string,
  data_fim: string,
  signal?: AbortSignal
): Promise<IntelligenceJobStatus> {
  const r = await api.get(`/bi/intelligence/status/${jobId}`, {
    params: { data_inicio, data_fim },
    signal,
  })
  return r.data
}

/**
 * Dismiss de insight (ignorar).
 */
export async function dismissInsightAPI(hash: string): Promise<void> {
  await api.post(`/bi/intelligence/${hash}/dismiss`)
}
