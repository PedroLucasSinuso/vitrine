/* eslint-disable react-hooks/set-state-in-effect -- Initial data load on mount */
import { useState, useEffect, useRef } from 'react'
import { triggerSync, getSyncStatus, getSyncHistory } from '../api/admin'
import AdminHeader from '../components/AdminHeader'
import type { SyncJob, SyncHistory } from '../types'
import { formatDate } from '../utils/formatters'
import { RefreshCw, Clock, CheckCircle2, XCircle, Loader2, Database, Hash, AlertCircle } from 'lucide-react'
import ErrorBanner from '../components/ui/ErrorBanner'
import EmptyState from '../components/ui/EmptyState'

function StatusBadge({ status }: { status: SyncJob['status'] }) {
  const styles: Record<string, string> = {
    sucesso: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    em_progresso: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    erro: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    started: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  }
  const labels: Record<string, string> = {
    sucesso: 'Sucesso',
    em_progresso: 'Em progresso',
    erro: 'Erro',
    started: 'Iniciando...',
  }
  const icons: Record<string, React.ReactNode> = {
    sucesso: <CheckCircle2 size={12} />,
    em_progresso: <Loader2 size={12} className="animate-spin" />,
    erro: <XCircle size={12} />,
    started: <Loader2 size={12} className="animate-spin" />,
  }
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${styles[status]}`}>
      {icons[status]}
      {labels[status]}
    </span>
  )
}

const statusIconMap: Record<string, React.ReactNode> = {
  sucesso: <CheckCircle2 size={16} className="text-emerald-500" />,
  em_progresso: <Loader2 size={16} className="text-amber-500 animate-spin" />,
  erro: <AlertCircle size={16} className="text-red-500" />,
  started: <Loader2 size={16} className="text-blue-500 animate-spin" />,
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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6 overflow-x-auto">

      {/* Header */}
      <AdminHeader titulo="Sync ETL" paginaAtual="sync" />

      {/* Sync action card */}
      <div className="w-full max-w-2xl flex flex-col gap-5">

        {/* Trigger sync */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center">
              <Database size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-800 dark:text-slate-100">Sincronização ETL</h2>
              <p className="text-xs text-slate-400 dark:text-slate-500">Atualize os dados do sistema</p>
            </div>
          </div>

          <button
            onClick={handleSync}
            disabled={loading}
            className="bg-primary hover:bg-primary-hover text-white font-semibold px-6 py-2.5 rounded-xl transition disabled:opacity-50 text-sm inline-flex items-center gap-2"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Sincronizando...' : 'Iniciar Sync'}
          </button>

          {erro && <ErrorBanner message={erro} />}

          {/* Active job status */}
          {activeJob && (
            <div className="mt-5 border-t border-slate-200 dark:border-slate-700 pt-5 flex flex-col gap-3">
              <div className="flex items-center gap-3">
                {statusIconMap[activeJob.status]}
                <StatusBadge status={activeJob.status} />
              </div>
              {activeJob.produtos_count != null && (
                <div className="flex gap-4 text-sm text-slate-600 dark:text-slate-400">
                  <span className="flex items-center gap-1.5">
                    <Database size={13} className="text-slate-400" />
                    Produtos: <span className="font-semibold text-slate-800 dark:text-slate-200">{activeJob.produtos_count}</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Hash size={13} className="text-slate-400" />
                    Códigos: <span className="font-semibold text-slate-800 dark:text-slate-200">{activeJob.codigos_count}</span>
                  </span>
                </div>
              )}
              {activeJob.finished_at && (
                <p className="text-xs text-slate-400 dark:text-slate-500 flex items-center gap-1.5">
                  <Clock size={12} /> Finalizado em {formatDate(activeJob.finished_at)}
                </p>
              )}
              {activeJob.error_message && (
                <p className="text-sm text-red-500 flex items-center gap-1.5" role="alert">
                  <AlertCircle size={14} /> {activeJob.error_message}
                </p>
              )}
            </div>
          )}
        </div>

        {/* History */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center">
              <Clock size={20} className="text-slate-500 dark:text-slate-400" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-800 dark:text-slate-100">
                Histórico de Sincronizações
              </h2>
              {history && (
                <p className="text-xs text-slate-400 dark:text-slate-500">{history.total} total</p>
              )}
            </div>
          </div>

          {!history && (
            <div className="flex items-center gap-2 text-sm text-slate-400 dark:text-slate-500 py-4">
              <Loader2 size={14} className="animate-spin" /> Carregando...
            </div>
          )}

          {history && history.jobs.length === 0 && (
            <EmptyState title="Nenhuma sincronização registrada" description="Inicie um sync para popular o histórico." />
          )}

          {history && history.jobs.length > 0 && (
            <div className="flex flex-col gap-2">
              {history.jobs.map((job, idx) => (
                <div key={job.job_id} className="flex items-center gap-3 border border-slate-200 dark:border-slate-700 rounded-xl p-3">
                  {/* Timeline dot */}
                  <div className="flex flex-col items-center shrink-0">
                    {statusIconMap[job.status]}
                    {idx < history.jobs.length - 1 && (
                      <div className="w-px h-4 bg-slate-200 dark:bg-slate-700 mt-1" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Job #{job.job_id}</span>
                      <StatusBadge status={job.status} />
                    </div>
                    <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
                      {formatDate(job.started_at)}
                      {job.finished_at && ` → ${formatDate(job.finished_at)}`}
                    </p>
                    {job.produtos_count != null && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        {job.produtos_count} produtos · {job.codigos_count} códigos
                      </p>
                    )}
                    {job.error_message && (
                      <p className="text-xs text-red-500 mt-1">{job.error_message}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
