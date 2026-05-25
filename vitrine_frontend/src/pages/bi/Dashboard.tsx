import { useState, useCallback, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import EmptyState from '../../components/ui/EmptyState'
import KpiCard from '../../components/bi/KpiCard'
import HeroKpiCard from '../../components/bi/HeroKpiCard'
import ErrorBanner from '../../components/ui/ErrorBanner'
import Card from '../../components/ui/Card'
import { fetchKpis, fetchKpisComparativo, fetchRanking, fetchDiario, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import { getConfigsCache } from '../../stores/configStore'
import type { KpisDTO, KpisComparativoDTO, ItemRankingDTO, PontoDiarioDTO, PeriodoBi } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { useCountUp } from '../../hooks/useCountUp'
import { CHART_THEME, formatChartCurrency, formatChartNumber } from '../../config/chartTheme'
import { Clock, TrendingUp, ArrowRight, RefreshCw, Target } from 'lucide-react'
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

function periodoMesAtual(): PeriodoBi {
  const hoje = new Date()
  return {
    data_inicio: format(hoje, 'yyyy-MM-01'),
    data_fim: format(hoje, 'yyyy-MM-dd'),
  }
}

function variacaoInfo(pct: number | null): { valor: number; direcao: 'positivo' | 'negativo' | 'estavel' } | null {
  if (pct === null) return null
  if (pct > 0) return { valor: pct, direcao: 'positivo' }
  if (pct < 0) return { valor: pct, direcao: 'negativo' }
  return { valor: 0, direcao: 'estavel' }
}

/** Format date string for chart ticks */
function formatDateTick(value: string): string {
  const d = new Date(value + 'T00:00:00')
  return format(d, 'dd/MM')
}

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

  // ── Meta / Projeção ──
  const [metaMensal, setMetaMensal] = useState<number | null>(null)
  const [receitaMesAtual, setReceitaMesAtual] = useState<number | null>(null)
  const [loadingMeta, setLoadingMeta] = useState(true)

  // ── Gráficos de tendência ──
  const [diarioTicketMedio, setDiarioTicketMedio] = useState<PontoDiarioDTO[]>([])
  const [diarioTickets, setDiarioTickets] = useState<PontoDiarioDTO[]>([])
  const [loadingDiario, setLoadingDiario] = useState(false)

  const kpisAtivos = kpisComp ?? kpis

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

  // ── Carregar meta + receita do mês atual ──
  useEffect(() => {
    getConfigsCache().then((c) => {
      const val = c.meta_faturamento_mensal
      if (val && Number(val) > 0) setMetaMensal(Number(val))
    }).catch(() => {})
    fetchKpis(periodoMesAtual())
      .then((k) => setReceitaMesAtual(k.faturamento_bruto))
      .catch(() => {})
      .finally(() => setLoadingMeta(false))
  }, [])

  // ── Carregar dados diários para os gráficos ──
  const buscarDiario = useCallback(async (p: PeriodoBi) => {
    // Só busca se período > 1 dia
    if (p.data_inicio === p.data_fim) {
      setDiarioTicketMedio([])
      setDiarioTickets([])
      return
    }
    setLoadingDiario(true)
    try {
      const [tm, qt] = await Promise.all([
        fetchDiario(p, 'ticket_medio'),
        fetchDiario(p, 'qtd_tickets'),
      ])
      setDiarioTicketMedio(tm)
      setDiarioTickets(qt)
    } catch {
      // silencioso
    } finally {
      setLoadingDiario(false)
    }
  }, [])

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    buscarDiario(p)
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
  }, [periodo, comparar, cache, cacheKey, buscarDiario])

  const isFirstRender = useRef(true)
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false
      buscar()
    } else {
      cache.invalidate(cacheKey)
      buscar(undefined, true)
    }
  }, [comparar]) // eslint-disable-line react-hooks/exhaustive-deps

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.invalidate(cacheKey)
    buscar(periodoOverride, true)
  }

  // ── Cálculos de meta / projeção ──
  const hoje = new Date()
  const diasCorridos = hoje.getDate()
  const ultimoDiaMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0).getDate()
  const pctMeta = metaMensal && receitaMesAtual ? (receitaMesAtual / metaMensal) * 100 : null
  const projecao = receitaMesAtual != null && diasCorridos > 0
    ? (receitaMesAtual / diasCorridos) * ultimoDiaMes
    : null
  const projecaoVsMeta = metaMensal && projecao ? ((projecao / metaMensal) * 100) - 100 : null

  // ── Estado vazio para gráficos ──
  const temGraficos = diarioTicketMedio.length > 1 || diarioTickets.length > 1

  return (
    <BiPageLayout titulo="BI" breadcrumb={[{ label: 'BI' }]}>
      {/* Top bar: periodo + controls */}
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
          <label className="flex items-center gap-1.5 text-sm text-text-muted cursor-pointer select-none">
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
              <span className="flex items-center gap-1.5 text-xs text-text-muted font-medium" title={`Cache atualizado às ${format(new Date(cacheTimestamp), 'HH:mm:ss')}`}>
                <RefreshCw size={12} className={cacheFresh ? 'text-success' : 'text-warning'} />
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
            <span className="text-xs text-warning bg-warning-light px-2.5 py-1 rounded-full">
              <Clock size={12} className="inline mr-1" /> Parcial até {kpisComp.dados_parciais_ate}
            </span>
          )}
        </div>
      </div>

      {erro && <ErrorBanner message={erro} />}

      {/* ── KPI section ── */}
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

          {/* Meta + Projeção — só se meta configurada */}
          {pctMeta != null && !loadingMeta && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* MetaCard */}
              <Card variant="bordered" padding="sm">
                <div className="flex items-center gap-2 mb-3">
                  <Target size={16} className="text-primary" />
                  <span className="text-xs font-semibold text-text-primary uppercase tracking-wider">Meta do Mês</span>
                </div>
                <div className="flex items-baseline gap-1.5 mb-2">
                  <span className="text-2xl font-bold text-text-primary">{pctMeta.toFixed(0)}%</span>
                  <span className="text-xs text-text-muted">atingido</span>
                </div>
                {/* Barra de progresso */}
                <div className="h-2 bg-bg-hover rounded-full overflow-hidden mb-2">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-primary-light rounded-full transition-all duration-700"
                    style={{ width: `${Math.min(pctMeta, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-text-muted">
                  <span className="font-semibold text-text-secondary">{formatCurrency(receitaMesAtual ?? 0)}</span>
                  {' / '}
                  <span>{formatCurrency(metaMensal ?? 0)}</span>
                </p>
              </Card>

              {/* ProjecaoCard */}
              <Card variant="bordered" padding="sm">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp size={16} className="text-primary" />
                  <span className="text-xs font-semibold text-text-primary uppercase tracking-wider">Projeção</span>
                </div>
                <div className="flex items-baseline gap-1.5 mb-1">
                  <span className="text-2xl font-bold text-text-primary">{formatCurrency(projecao ?? 0)}</span>
                </div>
                {projecaoVsMeta != null && (
                  <div className="flex items-center gap-1.5">
                    <span className={`text-xs font-semibold ${projecaoVsMeta >= 0 ? 'text-success' : 'text-danger'}`}>
                      {projecaoVsMeta >= 0 ? '▲' : '▼'} {Math.abs(projecaoVsMeta).toFixed(1)}% vs meta
                    </span>
                  </div>
                )}
                <p className="text-xs text-text-muted mt-1">
                  {diasCorridos} de {ultimoDiaMes} dias • {formatCurrency((receitaMesAtual ?? 0) / diasCorridos)}/dia
                </p>
              </Card>
            </div>
          )}

          {/* Secondary KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <KpiCard label="Faturamento Líquido" valor={formatCurrency(animFatLiq)} delay={80}
              variacao={kpisComp ? variacaoInfo(kpisComp.faturamento_liquido.variacao_pct) : null}
              valorAnterior={kpisComp?.faturamento_liquido.anterior != null ? formatCurrency(kpisComp.faturamento_liquido.anterior) : undefined} />
            <KpiCard label="Total de Trocas" valor={formatCurrency(animTrocas)} delay={160}
              variacao={kpisComp ? variacaoInfo(kpisComp.total_trocas.variacao_pct) : null} invertVariation
              valorAnterior={kpisComp?.total_trocas.anterior != null ? formatCurrency(kpisComp.total_trocas.anterior) : undefined} />
            <KpiCard label="Tickets" valor={Math.round(animTickets).toLocaleString('pt-BR')} delay={240}
              variacao={kpisComp ? variacaoInfo(kpisComp.qtd_tickets.variacao_pct) : null}
              valorAnterior={kpisComp?.qtd_tickets.anterior != null ? Math.round(kpisComp.qtd_tickets.anterior).toLocaleString('pt-BR') : undefined} />
            <KpiCard label="Ticket Médio" valor={formatCurrency(animTicketMedio)} delay={320}
              variacao={kpisComp ? variacaoInfo(kpisComp.ticket_medio.variacao_pct) : null}
              valorAnterior={kpisComp?.ticket_medio.anterior != null ? formatCurrency(kpisComp.ticket_medio.anterior) : undefined} />
            <KpiCard label="Itens por Ticket" valor={animItensTicket.toFixed(2)} delay={400}
              variacao={kpisComp ? variacaoInfo(kpisComp.itens_por_ticket.variacao_pct) : null}
              valorAnterior={kpisComp?.itens_por_ticket.anterior != null ? kpisComp.itens_por_ticket.anterior.toFixed(2) : undefined} />
          </div>
        </div>
      )}

      {!kpisAtivos && !loading && !erro && (
        <EmptyState title="Selecione um período" description="Escolha um período para analisar os dados." />
      )}

      {/* ── Gráficos de Tendência ── */}
      {temGraficos && (
        <Card variant="bordered" padding="md">
          <h2 className="text-sm font-semibold text-text-primary font-display flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-primary" />
            Tendências no Período
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Ticket Médio */}
            <div>
              <p className="text-xs text-text-muted mb-2 font-medium">Ticket Médio</p>
              <ResponsiveContainer width="100%" height={180}>
                <AreaChart data={diarioTicketMedio} margin={CHART_THEME.margin}>
                  <defs>
                    <linearGradient id="gradTm" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="data" tickFormatter={formatDateTick} {...CHART_THEME.xAxis} />
                  <YAxis {...CHART_THEME.yAxis} tickFormatter={formatChartCurrency} />
                  <Tooltip
                    cursor={CHART_THEME.tooltip.cursor}
                    contentStyle={CHART_THEME.tooltip.contentStyle}
                    formatter={((v: number) => formatCurrency(v)) as never}
                    labelFormatter={((l: string) => format(new Date(l + 'T00:00:00'), 'dd/MM/yyyy')) as never}
                  />
                  <Area
                    type="monotone"
                    dataKey="valor"
                    stroke="var(--color-primary)"
                    fill="url(#gradTm)"
                    strokeWidth={CHART_THEME.area.strokeWidth}
                    fillOpacity={CHART_THEME.area.fillOpacity}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            {/* Tickets */}
            <div>
              <p className="text-xs text-text-muted mb-2 font-medium">Tickets</p>
              <ResponsiveContainer width="100%" height={180}>
                <AreaChart data={diarioTickets} margin={CHART_THEME.margin}>
                  <defs>
                    <linearGradient id="gradTk" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-chart-2)" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="var(--color-chart-2)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="data" tickFormatter={formatDateTick} {...CHART_THEME.xAxis} />
                  <YAxis {...CHART_THEME.yAxis} tickFormatter={formatChartNumber} />
                  <Tooltip
                    cursor={CHART_THEME.tooltip.cursor}
                    contentStyle={CHART_THEME.tooltip.contentStyle}
                    formatter={((v: number) => (v ?? 0).toLocaleString('pt-BR')) as never}
                    labelFormatter={((l: string) => format(new Date(l + 'T00:00:00'), 'dd/MM/yyyy')) as never}
                  />
                  <Area
                    type="monotone"
                    dataKey="valor"
                    stroke="var(--color-chart-2)"
                    fill="url(#gradTk)"
                    strokeWidth={CHART_THEME.area.strokeWidth}
                    fillOpacity={CHART_THEME.area.fillOpacity}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Card>
      )}

      {/* ── Loading dos gráficos ── */}
      {loadingDiario && !temGraficos && periodo.data_inicio !== periodo.data_fim && (
        <Card variant="bordered" padding="md">
          <Skeleton className="h-5 w-48 mb-4" />
          <div className="grid grid-cols-2 gap-6">
            <Skeleton className="h-[180px] rounded-lg" />
            <Skeleton className="h-[180px] rounded-lg" />
          </div>
        </Card>
      )}

      {/* ── Mini Ranking Compacto ── */}
      {topProdutos.length > 0 && (
        <Card variant="bordered" padding="sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <TrendingUp size={15} className="text-primary" />
              <h2 className="text-sm font-semibold text-text-primary">Top Produtos</h2>
            </div>
            <button
              onClick={() => navigate('/bi/ranking')}
              className="text-xs text-primary hover:text-primary-hover font-medium flex items-center gap-1 transition"
            >
              Ver completo <ArrowRight size={12} />
            </button>
          </div>
          <div className="flex flex-col gap-1">
            {topProdutos.map((item, i) => (
              <div
                key={item.codigo}
                onClick={() => navigate(`/bi/sku?codigo=${item.codigo}`)}
                className="group flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-bg-hover cursor-pointer transition"
              >
                <span className="text-xs font-bold text-text-muted w-5 shrink-0 text-center">
                  {i + 1}
                </span>
                <span className="flex-1 text-sm text-text-primary truncate min-w-0" title={item.produto}>
                  {item.produto}
                </span>
                <span className="text-xs font-semibold text-text-primary shrink-0 tabular-nums">
                  {formatCurrency(item.valor)}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* ── Ranking Skeleton ── */}
      {loading && topProdutos.length === 0 && (
        <Card variant="bordered" padding="sm">
          <Skeleton className="h-5 w-36 mb-3" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 px-2 py-1.5">
              <Skeleton className="h-4 w-5" />
              <Skeleton className="h-4 flex-1" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </Card>
      )}
    </BiPageLayout>
  )
}
