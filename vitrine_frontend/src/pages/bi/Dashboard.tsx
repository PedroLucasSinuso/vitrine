import { useState, useCallback, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import EmptyState from '../../components/ui/EmptyState'
import KpiCard from '../../components/bi/KpiCard'
import HeroKpiCard from '../../components/bi/HeroKpiCard'
import ErrorBanner from '../../components/ui/ErrorBanner'
import { fetchKpis, fetchKpisComparativo, fetchRanking, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { KpisDTO, KpisComparativoDTO, ItemRankingDTO, PeriodoBi } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { useCountUp } from '../../hooks/useCountUp'
import { Clock, TrendingUp, ArrowRight, RefreshCw } from 'lucide-react'
import Skeleton from '../../components/ui/Skeleton'

const PRESETS_DASHBOARD: Preset[] = [
  { label: 'Hoje', kind: 'days', days: 0 },
  { label: '7 dias', kind: 'days', days: 7 },
  { label: '30 dias', kind: 'days', days: 30 },
  { label: 'Este mês', kind: 'current_month' },
  { label: 'Mês passado', kind: 'last_month' },
]

function periodoInicial(): PeriodoBi {
  const hoje = format(new Date(), 'yyyy-MM-dd')
  return { data_inicio: hoje, data_fim: hoje }
}

function variacaoInfo(pct: number | null): { valor: number; direcao: 'positivo' | 'negativo' | 'estavel' } | null {
  if (pct === null) return null
  if (pct > 0) return { valor: pct, direcao: 'positivo' }
  if (pct < 0) return { valor: pct, direcao: 'negativo' }
  return { valor: 0, direcao: 'estavel' }
}

const maxValor = (items: ItemRankingDTO[]) => Math.max(...items.map((i) => i.valor), 1)

export default function Dashboard() {
  const navigate = useNavigate()
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [comparar, setComparar] = useState(true)
  const [kpis, setKpis] = useState<KpisDTO | null>(null)
  const [kpisComp, setKpisComp] = useState<KpisComparativoDTO | null>(null)
  const [topProdutos, setTopProdutos] = useState<ItemRankingDTO[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [pulseKey, setPulseKey] = useState(0)

  const kpisAtivos = kpisComp ?? kpis
  const topMax = useMemo(() => maxValor(topProdutos), [topProdutos])

  const animFatBruto = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.faturamento_bruto.atual : (kpis as KpisDTO).faturamento_bruto) : 0, 600, !!kpisAtivos)
  const animFatLiq = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.faturamento_liquido.atual : (kpis as KpisDTO).faturamento_liquido) : 0, 600, !!kpisAtivos)
  const animTrocas = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.total_trocas.atual : (kpis as KpisDTO).total_trocas) : 0, 600, !!kpisAtivos)
  const animTicketMedio = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.ticket_medio.atual : (kpis as KpisDTO).ticket_medio) : 0, 600, !!kpisAtivos)
  const animTickets = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.qtd_tickets.atual : (kpis as KpisDTO).qtd_tickets) : 0, 600, !!kpisAtivos)
  const animItensTicket = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.itens_por_ticket.atual : (kpis as KpisDTO).itens_por_ticket) : 0, 600, !!kpisAtivos)
  const cache = useBiCache()
  const cacheKey = `dashboard_${comparar}`
  const cacheTimestamp = cache.getTimestamp(cacheKey, periodo)
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 30000); return () => clearInterval(t) }, [])
  const cacheFresh = cacheTimestamp ? cacheTimestamp > now - 300000 : false
  const { toast } = useToast()

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    if (!force) {
      const cached = cache.get<{ kpis: KpisDTO | KpisComparativoDTO; ranking: ItemRankingDTO[] }>(cacheKey, p)
      if (cached) {
        if (comparar && 'faturamento_bruto' in cached.kpis && 'atual' in (cached.kpis as KpisComparativoDTO).faturamento_bruto) {
          setKpisComp(cached.kpis as KpisComparativoDTO)
          setKpis(null)
        } else if (!comparar && 'faturamento_bruto' in cached.kpis && !('atual' in (cached.kpis as KpisComparativoDTO).faturamento_bruto)) {
          setKpis(cached.kpis as KpisDTO)
          setKpisComp(null)
        } else {
          cache.clear()
        }
        setTopProdutos(cached.ranking)
        setPulseKey((prev) => prev + 1)
        return
      }
    }
    setErro(null)
    setLoading(true)
    try {
      const kpisPromise = comparar ? fetchKpisComparativo(p) : fetchKpis(p)
      const rankingPromise = fetchRanking(p, 'receita_produto', 5)
      const [kpisData, rankingData] = await Promise.all([kpisPromise, rankingPromise])
      if (comparar) {
        setKpisComp(kpisData as KpisComparativoDTO)
        setKpis(null)
      } else {
        setKpis(kpisData as KpisDTO)
        setKpisComp(null)
      }
      setTopProdutos(rankingData)
      cache.set(cacheKey, p, { kpis: kpisData, ranking: rankingData })
      setPulseKey((prev) => prev + 1)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados. Verifique a conexão com o servidor.')
    } finally {
      setLoading(false)
    }
  }, [periodo, comparar, cache, cacheKey])

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Re-fetch when "comparar" toggle changes
  useEffect(() => {
    cache.invalidate(cacheKey)
    const t = setTimeout(() => buscar(undefined, true)); return () => clearTimeout(t)
  }, [comparar]) // eslint-disable-line react-hooks/exhaustive-deps -- Intentional: re-fetch on toggle change

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.invalidate(cacheKey)
    buscar(periodoOverride, true)
  }

  return (
    <BiPageLayout titulo="BI" breadcrumb={[{ label: 'BI' }]}>
      {/* Top bar: periodo + controls side by side */}
      <div className="flex flex-col md:flex-row md:items-start gap-4 md:gap-6">
        <div className="flex-1 min-w-0">
          <PeriodoForm
            value={periodo}
            onChange={setPeriodo}
            onBuscar={handleBuscar}
            loading={loading}
            presets={PRESETS_DASHBOARD}
          />
        </div>
        <div className="flex flex-col gap-3 md:items-end md:pt-1 shrink-0">
          <label className="flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={comparar}
              onChange={(e) => setComparar(e.target.checked)}
              className="accent-primary w-4 h-4 rounded"
            />
            Comparar com ano anterior
          </label>
          <div className="flex items-center gap-3">
            {cacheTimestamp && (
              <span className="flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500" title={`Cache atualizado às ${format(new Date(cacheTimestamp), 'HH:mm:ss')}`}>
                <RefreshCw size={10} className={cacheFresh ? 'text-emerald-500' : 'text-amber-500'} />
                {formatDistanceToNow(new Date(cacheTimestamp), { locale: ptBR, addSuffix: true })}
              </span>
            )}
            <ExportButtons
              onExcel={() => { exportarExcelBI(periodo, 'kpis'); toast({ type: 'success', message: 'Excel exportado' }) }}
              onCsv={() => { if (kpisAtivos) { baixarCSVdeArray([kpisAtivos], 'kpis'); toast({ type: 'success', message: 'CSV exportado' }) } }}
              disabled={!kpisAtivos}
            />
          </div>
          {kpisComp?.dados_parciais_ate && (
            <span className="text-xs text-amber-600 bg-amber-50 dark:bg-amber-900/30 dark:text-amber-400 px-2.5 py-1 rounded-full">
              <Clock size={12} className="inline mr-1" /> Parcial até {kpisComp.dados_parciais_ate}
            </span>
          )}
        </div>
      </div>

      {erro && <ErrorBanner message={erro} />}

      {/* Loading skeleton */}
      {loading && !kpisAtivos && (
        <div className="flex flex-col gap-4">
          {/* Hero skeleton */}
          <Skeleton variant="kpi" className="h-36" />
          {/* KPI grid skeleton */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} variant="kpi" />
            ))}
          </div>
          {/* Ranking skeleton */}
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 p-5">
            <Skeleton className="h-5 w-40 mb-4" />
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 mb-3">
                <Skeleton className="h-6 w-6 rounded-full" />
                <Skeleton className="h-4 flex-1" />
                <Skeleton className="h-4 w-20" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* KPI section */}
      {kpisAtivos && (
        <div className="flex flex-col gap-4">
          {/* Hero KPI */}
          <HeroKpiCard
            label="Faturamento Bruto"
            valor={formatCurrency(animFatBruto)}
            pulseKey={pulseKey}
            variacao={kpisComp ? variacaoInfo(kpisComp.faturamento_bruto.variacao_pct) : null}
            valorAnterior={kpisComp?.faturamento_bruto.anterior != null ? formatCurrency(kpisComp.faturamento_bruto.anterior) : undefined}
          />
          {/* Secondary KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            <KpiCard label="Faturamento Líquido" valor={formatCurrency(animFatLiq)} delay={80} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.faturamento_liquido.variacao_pct) : null}
              valorAnterior={kpisComp?.faturamento_liquido.anterior != null ? formatCurrency(kpisComp.faturamento_liquido.anterior) : undefined} />
            <KpiCard label="Total de Trocas" valor={formatCurrency(animTrocas)} delay={160} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.total_trocas.variacao_pct) : null} invertVariation
              valorAnterior={kpisComp?.total_trocas.anterior != null ? formatCurrency(kpisComp.total_trocas.anterior) : undefined} />
            <KpiCard label="Tickets" valor={Math.round(animTickets).toLocaleString('pt-BR')} delay={240} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.qtd_tickets.variacao_pct) : null}
              valorAnterior={kpisComp?.qtd_tickets.anterior != null ? Math.round(kpisComp.qtd_tickets.anterior).toLocaleString('pt-BR') : undefined} />
            <KpiCard label="Ticket Médio" valor={formatCurrency(animTicketMedio)} delay={320} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.ticket_medio.variacao_pct) : null}
              valorAnterior={kpisComp?.ticket_medio.anterior != null ? formatCurrency(kpisComp.ticket_medio.anterior) : undefined} />
            <KpiCard label="Itens por Ticket" valor={animItensTicket.toFixed(2)} delay={400} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.itens_por_ticket.variacao_pct) : null}
              valorAnterior={kpisComp?.itens_por_ticket.anterior != null ? kpisComp.itens_por_ticket.anterior.toFixed(2) : undefined} />
          </div>
        </div>
      )}

      {!kpisAtivos && !loading && !erro && (
        <EmptyState title="Selecione um período" description="Escolha um período para analisar os dados." />
      )}

      {/* Top 5 Ranking */}
      {loading && topProdutos.length === 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 p-5">
          <Skeleton className="h-5 w-48 mb-4" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 mb-3">
              <Skeleton className="h-6 w-6 rounded-full" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-4 w-20" />
            </div>
          ))}
        </div>
      )}
      {topProdutos.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-primary" />
              <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Top 5 Produtos</h2>
            </div>
            <button
              onClick={() => navigate('/bi/ranking')}
              className="text-xs text-primary hover:text-primary-hover font-medium flex items-center gap-1 transition"
            >
              Ver completo <ArrowRight size={12} />
            </button>
          </div>
          <div className="flex flex-col gap-2">
            {topProdutos.map((item, i) => {
              const pct = (item.valor / topMax) * 100
              return (
                <div
                  key={item.codigo}
                  onClick={() => navigate(`/bi/sku?codigo=${item.codigo}`)}
                  className="group flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition"
                >
                  <span className="text-xs font-bold text-slate-300 dark:text-slate-600 w-5 shrink-0 text-center">
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono text-slate-400 dark:text-slate-500 shrink-0">{item.codigo}</span>
                      <span className="text-sm text-slate-700 dark:text-slate-300 truncate" title={item.produto}>
                        {item.produto}
                      </span>
                    </div>
                    <div className="h-1.5 bg-slate-50 dark:bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-primary to-primary-light rounded-full transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-sm font-semibold text-slate-800 dark:text-slate-100 shrink-0">
                    {formatCurrency(item.valor)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </BiPageLayout>
  )
}
