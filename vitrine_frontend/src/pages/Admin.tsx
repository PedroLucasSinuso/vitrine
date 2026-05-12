/* eslint-disable react-hooks/set-state-in-effect -- Initial data load on mount */
import { useState, useEffect, useRef } from 'react'
import { triggerSync, getSyncStatus, getSyncHistory } from '../api/admin'
import AdminHeader from '../components/AdminHeader'
import type { SyncJob, SyncHistory } from '../types'
import { formatDate } from '../utils/formatters'

function StatusBadge({ status }: { status: SyncJob['status'] }) {
  const styles: Record<string, string> = {
    sucesso: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    em_progresso: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    erro: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    started: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  }
  const labels: Record<string, string> = {
    sucesso: 'Sucesso',
    em_progresso: 'Em progresso',
    erro: 'Erro',
    started: 'Iniciando...',
  }
  return (
    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${styles[status]}`}>
      {labels[status]}
    </span>
  )
}

export default function Admin() {
  const [history, setHistory] = useState<SyncHistory | null>(null)
  const [activeJob, setActiveJob] = useState<SyncJob | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  async function carregarHistorico() {
    try {
      const data = await getSyncHistory()
      setHistory(data)
    } catch {
      setErro('Erro ao carregar histórico.')
    }
  }

  useEffect(() => {
    carregarHistorico()
  }, [])

  function pararPolling() {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }

  async function handleSync() {
    setErro('')
    setLoading(true)
    setActiveJob(null)
    try {
      const { job_id } = await triggerSync()

      pollingRef.current = setInterval(async () => {
        abortControllerRef.current = new AbortController()
        try {
          const status: SyncJob = await getSyncStatus(job_id, abortControllerRef.current.signal)
          setActiveJob(status)
          if (status.status !== 'em_progresso') {
            pararPolling()
            setLoading(false)
            carregarHistorico()
          }
        } catch (e: unknown) {
          if ((e as Error).name === 'AbortError') return
          pararPolling()
          setLoading(false)
          setErro('Erro ao verificar status do sync.')
        }
      }, 2000)

    } catch {
      setLoading(false)
      setErro('Erro ao iniciar sync.')
    }
  }

  useEffect(() => () => pararPolling(), [])

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">

      {/* Header */}
      <AdminHeader titulo="Sync ETL" paginaAtual="sync" />

      {/* Trigger sync */}
      <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5 mb-6">
        <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Sincronização ETL</h2>

        <button
          onClick={handleSync}
          disabled={loading}
          className="bg-primary hover:bg-primary-hover text-white font-semibold px-6 py-2 rounded-lg transition disabled:opacity-50"
        >
          {loading ? 'Sincronizando...' : 'Iniciar Sync'}
        </button>

        {erro && <p className="text-red-500 text-sm mt-3" role="alert">{erro}</p>}

        {/* Status do job ativo */}
        {activeJob && (
          <div className="mt-4 border-t dark:border-gray-700 pt-4 flex flex-col gap-2">
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600 dark:text-gray-400">Status:</span>
              <StatusBadge status={activeJob.status} />
            </div>
            {activeJob.produtos_count != null && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Produtos: <span className="font-semibold">{activeJob.produtos_count}</span>
                {' · '}
                Códigos: <span className="font-semibold">{activeJob.codigos_count}</span>
              </p>
            )}
            {activeJob.finished_at && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Finalizado em: <span className="font-semibold">{formatDate(activeJob.finished_at)}</span>
              </p>
            )}
            {activeJob.error_message && (
              <p className="text-sm text-red-500" role="alert">{activeJob.error_message}</p>
            )}
          </div>
        )}
      </div>

      {/* Histórico */}
      <div className="w-full max-w-2xl bg-white dark:bg-gray-800 rounded-2xl shadow-md p-5">
        <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">
          Histórico de Sincronizações
          {history && <span className="text-gray-400 dark:text-gray-500 font-normal text-sm ml-2">({history.total} total)</span>}
        </h2>

        {!history && <p className="text-sm text-gray-400 dark:text-gray-500">Carregando...</p>}

        {history && history.jobs.length === 0 && (
          <p className="text-sm text-gray-400 dark:text-gray-500">Nenhuma sincronização registrada.</p>
        )}

        {history && history.jobs.length > 0 && (
          <div className="flex flex-col gap-3">
            {history.jobs.map((job) => (
              <div key={job.job_id} className="border dark:border-gray-700 rounded-lg p-4 flex flex-col gap-1">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500 dark:text-gray-400">Job #{job.job_id}</span>
                  <StatusBadge status={job.status} />
                </div>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  Iniciado: {formatDate(job.started_at)}
                  {job.finished_at && ` · Finalizado: ${formatDate(job.finished_at)}`}
                </p>
                {job.produtos_count != null && (
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {job.produtos_count} produtos · {job.codigos_count} códigos
                  </p>
                )}
                {job.error_message && (
                  <p className="text-xs text-red-500" role="alert">{job.error_message}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
