/* eslint-disable react-hooks/set-state-in-effect -- Initial data load on mount */
import { useState, useEffect, useRef } from 'react'
import { triggerSync, getSyncStatus, getSyncHistory } from '../api/admin'
import type { SyncJob, SyncHistory } from '../types'
import { formatDate } from '../utils/formatters'
import { RefreshCw, Clock, CheckCircle2, Loader2, Database, Hash, AlertCircle } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import ErrorBanner from '../components/ui/ErrorBanner'
import EmptyState from '../components/ui/EmptyState'

const statusIconMap: Record<string, React.ReactNode> = {
  sucesso: <CheckCircle2 size={16} className="text-success" />,
  em_progresso: <Loader2 size={16} className="text-warning animate-spin" />,
  erro: <AlertCircle size={16} className="text-danger" />,
  started: <Loader2 size={16} className="text-info animate-spin" />,
}

const statusToBadge: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
  sucesso: 'success',
  em_progresso: 'warning',
  erro: 'danger',
  started: 'info',
}

export default function Admin() {
  const [history, setHistory] = useState<SyncHistory | null>(null)
  const [activeJob, setActiveJob] = useState<SyncJob | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const mountedRef = useRef(true)

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

      // Se o componente foi desmontado enquanto triggerSync() rodava, não criar o intervalo
      if (!mountedRef.current) return

      pollingRef.current = setInterval(async () => {
        if (!mountedRef.current) {
          clearInterval(pollingRef.current!)
          pollingRef.current = null
          return
        }
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

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      pararPolling()
    }
  }, [])

  return (
    <div className="flex flex-col items-center px-4 py-4 overflow-x-auto">
      <div className="w-full max-w-2xl flex flex-col gap-5">
        {/* Trigger sync */}
        <Card variant="elevated" className="p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center">
              <Database size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-text-primary">Sincronização ETL</h2>
              <p className="text-xs text-text-muted">Atualize os dados do sistema</p>
            </div>
          </div>

          <Button onClick={handleSync} loading={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Sincronizando...' : 'Iniciar Sync'}
          </Button>

          {erro && <div className="mt-4"><ErrorBanner message={erro} /></div>}

          {/* Active job status */}
          {activeJob && (
            <div className="mt-5 border-t border-border pt-5 flex flex-col gap-3">
              <div className="flex items-center gap-3">
                {statusIconMap[activeJob.status]}
                <Badge variant={statusToBadge[activeJob.status]} dot>
                  {activeJob.status === 'sucesso' ? 'Sucesso'
                    : activeJob.status === 'em_progresso' ? 'Em progresso'
                    : activeJob.status === 'erro' ? 'Erro'
                    : 'Iniciando...'}
                </Badge>
              </div>
              {activeJob.produtos_count != null && (
                <div className="flex gap-4 text-sm text-text-secondary flex-wrap">
                  <span className="flex items-center gap-1.5">
                    <Database size={13} className="text-text-muted" />
                    Produtos: <span className="font-semibold text-text-primary">{activeJob.produtos_count}</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Hash size={13} className="text-text-muted" />
                    Códigos: <span className="font-semibold text-text-primary">{activeJob.codigos_count}</span>
                  </span>
                </div>
              )}
              {activeJob.finished_at && (
                <p className="text-xs text-text-muted flex items-center gap-1.5">
                  <Clock size={12} /> Finalizado em {formatDate(activeJob.finished_at)}
                </p>
              )}
              {activeJob.error_message && (
                <p className="text-sm text-danger flex items-center gap-1.5" role="alert">
                  <AlertCircle size={14} /> {activeJob.error_message}
                </p>
              )}
            </div>
          )}
        </Card>

        {/* History */}
        <Card variant="elevated" className="p-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-bg-card flex items-center justify-center">
              <Clock size={20} className="text-text-muted" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-text-primary">
                Histórico de Sincronizações
              </h2>
              {history && (
                <p className="text-xs text-text-muted">{history.total} total</p>
              )}
            </div>
          </div>

          {!history && (
            <div className="flex items-center gap-2 text-sm text-text-muted py-4">
              <Loader2 size={14} className="animate-spin" /> Carregando...
            </div>
          )}

          {history && history.jobs.length === 0 && (
            <EmptyState title="Nenhuma sincronização registrada" description="Inicie um sync para popular o histórico." />
          )}

          {history && history.jobs.length > 0 && (
            <div className="flex flex-col gap-2">
              {history.jobs.map((job, idx) => (
                <div key={job.job_id} className="flex items-center gap-3 border border-border rounded-xl p-3">
                  {/* Timeline dot */}
                  <div className="flex flex-col items-center shrink-0">
                    {statusIconMap[job.status]}
                    {idx < history.jobs.length - 1 && (
                      <div className="w-px h-4 bg-border mt-1" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-text-primary">Job #{job.job_id}</span>
                      <Badge variant={statusToBadge[job.status]} dot>
                        {job.status === 'sucesso' ? 'Sucesso'
                          : job.status === 'em_progresso' ? 'Em progresso'
                          : job.status === 'erro' ? 'Erro'
                          : 'Iniciando...'}
                      </Badge>
                    </div>
                    <p className="text-xs text-text-muted mt-0.5">
                      {formatDate(job.started_at)}
                      {job.finished_at && ` → ${formatDate(job.finished_at)}`}
                    </p>
                    {job.produtos_count != null && (
                      <p className="text-xs text-text-muted mt-0.5">
                        {job.produtos_count} produtos · {job.codigos_count} códigos
                      </p>
                    )}
                    {job.error_message && (
                      <p className="text-xs text-danger mt-1">{job.error_message}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
