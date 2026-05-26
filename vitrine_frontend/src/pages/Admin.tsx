/* eslint-disable react-hooks/set-state-in-effect -- Initial data load on mount */
import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { triggerSync, getSyncStatus, getSyncHistory, getStatus, getCacheStatus } from '../api/admin'
import type { SyncJob, SyncHistory } from '../types'
import { formatDate } from '../utils/formatters'
import {
  RefreshCw, Clock, CheckCircle2, Loader2, Database, Hash, AlertCircle,
  Activity, Settings, Users, Tags, Shield, ArrowRight,
} from 'lucide-react'
import PageContainer from '../components/layout/PageContainer'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import ErrorBanner from '../components/ui/ErrorBanner'


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

interface QuickLink {
  label: string
  path: string
  icon: React.ReactNode
  description: string
}

const QUICK_LINKS: QuickLink[] = [
  { label: 'Configurações', path: '/admin/configuracoes', icon: <Settings size={18} />, description: 'ERP, WhatsApp, E-mail, IA' },
  { label: 'Usuários', path: '/admin/usuarios', icon: <Users size={18} />, description: 'Gerenciar contas e permissões' },
  { label: 'Etiquetas', path: '/admin/etiquetas', icon: <Tags size={18} />, description: 'Impressão de etiquetas' },
]

export default function Admin() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<SyncHistory | null>(null)
  const [activeJob, setActiveJob] = useState<SyncJob | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const mountedRef = useRef(true)

  // System status
  const [statusLastUpdated, setStatusLastUpdated] = useState<string | null>(null)
  const [cacheInfo, setCacheInfo] = useState<{ produtos_cached?: boolean; last_refresh?: string; ttl_seconds?: number } | null>(null)

  async function carregarHistorico() {
    try {
      const data = await getSyncHistory()
      setHistory(data)
    } catch {
      setErro('Erro ao carregar histórico.')
    }
  }

  async function carregarStatus() {
    try {
      const [s, c] = await Promise.all([
        getStatus().catch(() => null),
        getCacheStatus().catch(() => null),
      ])
      if (s) setStatusLastUpdated(s.last_updated)
      if (c) setCacheInfo(c as typeof cacheInfo)
    } catch { /* ignore */ }
  }

  useEffect(() => {
    carregarHistorico()
    carregarStatus()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function pararPolling() {
    if (pollingRef.current) {
      clearTimeout(pollingRef.current)
      pollingRef.current = null
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }

  async function pollSync(job_id: string) {
    if (!mountedRef.current) return

    abortControllerRef.current = new AbortController()
    try {
      const status: SyncJob = await getSyncStatus(job_id, abortControllerRef.current.signal)
      if (!mountedRef.current) return
      setActiveJob(status)
      if (status.status !== 'em_progresso') {
        pararPolling()
        setLoading(false)
        carregarHistorico()
        carregarStatus()
        return
      }
      // Ainda em progresso — agenda próxima verificação
      pollingRef.current = window.setTimeout(() => pollSync(job_id), 2000)
    } catch (e: unknown) {
      const err = e as Error & { code?: string }
      // Axios usa CanceledError quando abatido, e o nome do erro não é 'AbortError'
      if (err.name === 'AbortError' || err.name === 'CanceledError' || err.code === 'ERR_CANCELED') return
      pararPolling()
      setLoading(false)
      setErro('Erro ao verificar status do sync.')
    }
  }

  async function handleSync() {
    pararPolling()
    setErro('')
    setLoading(true)
    setActiveJob(null)
    try {
      const { job_id } = await triggerSync()
      if (!mountedRef.current) return

      pollingRef.current = window.setTimeout(() => pollSync(job_id), 2000)
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
    <PageContainer maxWidth="lg">
      <div className="flex flex-col gap-5">
        {/* ── Hero ── */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center">
            <Shield size={20} className="text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-text-primary">Administração</h1>
            <p className="text-xs text-text-muted">Sincronização, status e configurações do sistema</p>
          </div>
        </div>

        {/* ── Grid: Sync + Status ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Sync card */}
          <Card variant="elevated" padding="lg">
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
                      <Database size={13} className="text-text-muted" /> Produtos: <span className="font-semibold text-text-primary">{activeJob.produtos_count}</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Hash size={13} className="text-text-muted" /> Códigos: <span className="font-semibold text-text-primary">{activeJob.codigos_count}</span>
                    </span>
                  </div>
                )}
                {activeJob.finished_at && (
                  <p className="text-xs text-text-muted flex items-center gap-1.5"><Clock size={12} /> Finalizado em {formatDate(activeJob.finished_at)}</p>
                )}
                {activeJob.error_message && (
                  <p className="text-sm text-danger flex items-center gap-1.5" role="alert"><AlertCircle size={14} /> {activeJob.error_message}</p>
                )}
              </div>
            )}
          </Card>

          {/* System status card */}
          <Card variant="elevated" padding="lg">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-bg-card flex items-center justify-center">
                <Activity size={20} className="text-text-muted" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-text-primary">Status do Sistema</h2>
                <p className="text-xs text-text-muted">Sincronização e cache</p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* ETL */}
              <div className="rounded-xl border border-border/50 bg-bg-hover/30 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1 rounded-md bg-emerald-500/10 text-emerald-500"><Activity size={12} /></div>
                  <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">Última sincronia</span>
                </div>
                <p className="text-sm font-mono text-text-primary">
                  {statusLastUpdated
                    ? new Date(statusLastUpdated).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
                    : '—'}
                </p>
              </div>

              {/* Cache */}
              <div className="rounded-xl border border-border/50 bg-bg-hover/30 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`p-1 rounded-md ${cacheInfo?.produtos_cached ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>
                    <Database size={12} />
                  </div>
                  <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wide">Cache</span>
                </div>
                {cacheInfo ? (
                  <div className="text-xs text-text-secondary space-y-1">
                    <p><span className="text-text-muted">Status: </span>
                      <span className={cacheInfo.produtos_cached ? 'text-success' : 'text-amber-600 dark:text-amber-400'}>
                        {cacheInfo.produtos_cached ? 'Ativo' : 'Vazio'}
                      </span>
                    </p>
                    {cacheInfo.last_refresh && <p><span className="text-text-muted">Atualização: </span>{new Date(cacheInfo.last_refresh).toLocaleString('pt-BR')}</p>}
                    {cacheInfo.ttl_seconds != null && <p><span className="text-text-muted">TTL: </span>{cacheInfo.ttl_seconds}s</p>}
                  </div>
                ) : (
                  <p className="text-xs text-text-muted">—</p>
                )}
              </div>
            </div>

            {/* Sync history mini-preview */}
            {history && history.jobs.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-text-muted uppercase tracking-wide">Últimas sincronizações</span>
                  <span className="text-[10px] text-text-muted">{history.total} total</span>
                </div>
                <div className="flex flex-col gap-1.5">
                  {history.jobs.slice(0, 3).map((job) => (
                    <div key={job.job_id} className="flex items-center gap-2.5 text-xs">
                      {statusIconMap[job.status]}
                      <span className="text-text-muted">{formatDate(job.started_at)}</span>
                      {job.produtos_count != null && (
                        <span className="text-text-muted">{job.produtos_count} produtos</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* ── Quick Links ── */}
        <Card variant="default" padding="md">
          <h2 className="text-sm font-semibold text-text-primary mb-4">Acesso rápido</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {QUICK_LINKS.map((link) => (
              <button
                key={link.path}
                onClick={() => navigate(link.path)}
                className="flex items-center gap-3 p-4 rounded-xl border border-border hover:border-primary/30 hover:bg-primary-lighter transition text-left group"
              >
                <div className="p-2 rounded-lg bg-primary-light text-primary shrink-0">
                  {link.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-text-primary group-hover:text-primary transition">{link.label}</p>
                  <p className="text-[11px] text-text-muted">{link.description}</p>
                </div>
                <ArrowRight size={14} className="text-text-muted group-hover:text-primary shrink-0 transition" />
              </button>
            ))}
          </div>
        </Card>
      </div>
    </PageContainer>
  )
}
