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
import SectionHeader from '../../components/ui/SectionHeader'
import Skeleton from '../../components/ui/Skeleton'
import { fetchKpis, fetchKpisComparativo, fetchRanking, fetchDiario, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import { getConfigsCache } from '../../stores/configStore'
import type { KpisDTO, KpisComparativoDTO, ItemRankingDTO, PontoDiarioDTO, PeriodoBi } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { useCountUp } from '../../hooks/useCountUp'
import { CHART_THEME, formatChartCurrency, formatChartNumber } from '../../config/chartTheme'
import { Clock, TrendingUp, ArrowRight, RefreshCw, BarChart3 } from 'lucide-react'

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

  // Determina qual fonte de dados usar (comparativo ou simples)
  const kpisAtivos = kpisComp ?? kpis
  const temComparativo = !!kpisComp

  // Animações countUp
  const animFatBrutoOrig = (() => {
    if (!kpisAtivos) return 0
    if (temComparativo) return (kpisAtivos as KpisComparativoDTO).faturamento_bruto.atual
    return (kpisAtivos as KpisDTO).faturamento_bruto
  })()
  const animFatBruto = useCountUp(animFatBrutoOrig, 600, !!kpisAtivos)

  type KpiKeys = 'faturamento_bruto' | 'faturamento_liquido' | 'total_trocas' | 'qtd_tickets' | 'ticket_medio' | 'itens_por_ticket'
  const getKpi = useCallback((key: KpiKeys): number => {
    if (!kpisAtivos) return 0
    if (temComparativo) {
      const comp = kpisAtivos as KpisComparativoDTO
      return comp[key]?.atual ?? 0
    }
    return (kpisAtivos as KpisDTO)[key] ?? 0
  }, [kpisAtivos, temComparativo])

  const getVariacao = useCallback((key: KpiKeys): number | null => {
    if (!temComparativo) return null
    const comp = kpisAtivos as KpisComparativoDTO
    return comp[key]?.variacao_pct ?? null
  }, [kpisAtivos, temComparativo])

  const getAnterior = useCallback((key: KpiKeys): number | null => {
    if (!temComparativo) return null
    const comp = kpisAtivos as KpisComparativoDTO
    return comp[key]?.anterior ?? null
  }, [kpisAtivos, temComparativo])

  const animFatLiq = useCountUp(getKpi('faturamento_liquido'), 600, !!kpisAtivos)
  const animTrocas = useCountUp(getKpi('total_trocas'), 600, !!kpisAtivos)
  const animTicketMedio = useCountUp(getKpi('ticket_medio'), 600, !!kpisAtivos)
  const animTickets = useCountUp(getKpi('qtd_tickets'), 600, !!kpisAtivos)
  const animItensTicket = useCountUp(getKpi('itens_por_ticket'), 600, !!kpisAtivos)

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
    <BiPageLayout titulo="Dashboard" breadcrumb={[{ label: 'BI' }, { label: 'Dashboard' }]}>
      {/* ============================================================ */}
      {/* TOP BAR — Periodo + Controls + Status                        */}
      {/* ============================================================ */}
      <Card variant="bordered" padding="sm">
        <div className="flex flex-col sm:flex-row sm:items-start gap-3">
          {/* Left: periodo form */}
          <div className="flex-1 min-w-0">
            <PeriodoForm
              value={periodo}
              onChange={setPeriodo}
              onBuscar={handleBuscar}
              loading={loading}
              presets={PRESETS_DASHBOARD}
            />
          </div>

          {/* Right: controls + status */}
          <div className="flex flex-col gap-2 sm:items-end sm:pt-1 shrink-0">
            {/* Comparar toggle pill */}
            <button
              onClick={() => setComparar((prev) => !prev)}
              className={`
                text-xs font-semibold px-3 py-1.5 rounded-full transition-all
                ${comparar
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-bg-hover text-text-secondary hover:bg-primary-lighter hover:text-primary'
                }
              `}
            >
              {comparar ? 'Comparando com ano anterior' : 'Comparar com ano anterior'}
            </button>

            {/* Cache freshness + Export */}
            <div className="flex items-center gap-3">
              {cacheTimestamp && (
                <span
                  className="flex items-center gap-1.5 text-xs text-text-muted font-medium"
                  title={`Cache atualizado às ${format(new Date(cacheTimestamp), 'HH:mm:ss')}`}
                >
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
      </Card>

      {erro && <ErrorBanner message={erro} />}

      {/* ============================================================ */}
      {/* MAIN CONTENT — KPI Hero + Secondary KPIs                     */}
      {/* ============================================================ */}
      {kpisAtivos && (
        <>
          {/* ── HERO: Faturamento Bruto (com meta + projeção inline) ── */}
          <HeroKpiCard
            label="Faturamento Bruto"
            valor={formatCurrency(animFatBruto)}
            pulseKey={pulseKey}
            variacao={temComparativo ? variacaoInfo(getVariacao('faturamento_bruto')) : null}
            valorAnterior={getAnterior('faturamento_bruto') != null ? formatCurrency(getAnterior('faturamento_bruto')!) : undefined}
            meta={!loadingMeta && pctMeta != null ? {
              pct: pctMeta,
              atual: receitaMesAtual ?? 0,
              meta: metaMensal ?? 0,
            } : null}
            projecao={!loadingMeta && projecao != null ? {
              valor: projecao,
              vsMetaPct: projecaoVsMeta,
              diasCorridos,
              diasTotal: ultimoDiaMes,
              mediaDiaria: receitaMesAtual != null && diasCorridos > 0 ? receitaMesAtual / diasCorridos : 0,
            } : null}
          />

          {/* ── Secondary KPIs (4 cards) ── */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <KpiCard
              label="Faturamento Líquido"
              valor={formatCurrency(animFatLiq)}
              delay={80}
              variacao={temComparativo ? variacaoInfo(getVariacao('faturamento_liquido')) : null}
              valorAnterior={getAnterior('faturamento_liquido') != null ? formatCurrency(getAnterior('faturamento_liquido')!) : undefined}
            />
            <KpiCard
              label="Total de Trocas"
              valor={formatCurrency(animTrocas)}
              delay={160}
              variacao={temComparativo ? variacaoInfo(getVariacao('total_trocas')) : null}
              invertVariation
              valorAnterior={getAnterior('total_trocas') != null ? formatCurrency(getAnterior('total_trocas')!) : undefined}
            />
            <KpiCard
              label="Tickets"
              valor={Math.round(animTickets).toLocaleString('pt-BR')}
              delay={240}
              variacao={temComparativo ? variacaoInfo(getVariacao('qtd_tickets')) : null}
              valorAnterior={getAnterior('qtd_tickets') != null ? Math.round(getAnterior('qtd_tickets')!).toLocaleString('pt-BR') : undefined}
            />
            <KpiCard
              label="Ticket Médio"
              valor={formatCurrency(animTicketMedio)}
              delay={320}
              variacao={temComparativo ? variacaoInfo(getVariacao('ticket_medio')) : null}
              valorAnterior={getAnterior('ticket_medio') != null ? formatCurrency(getAnterior('ticket_medio')!) : undefined}
            />
          </div>
        </>
      )}

      {/* ── Loading skeleton ── */}
      {loading && !kpisAtivos && !erro && (
        <div className="flex flex-col gap-4">
          <Skeleton variant="kpi" className="h-40" />
          <div className="grid grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} variant="kpi" />
            ))}
          </div>
        </div>
      )}

      {/* ── Empty state ── */}
      {!kpisAtivos && !loading && !erro && (
        <EmptyState title="Selecione um período" description="Escolha um período para analisar os dados." />
      )}

      {/* ============================================================ */}
      {/* CHARTS + RANKING — Side-by-side on desktop                    */}
      {/* ============================================================ */}
      {(temGraficos || loadingDiario || topProdutos.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* ── Charts (2/3 width) ── */}
          <div className="lg:col-span-2">
            {temGraficos ? (
              <Card variant="bordered" padding="md">
                <SectionHeader icon={TrendingUp}>Tendências no Período</SectionHeader>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
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
            ) : loadingDiario ? (
              <Card variant="bordered" padding="md">
                <Skeleton className="h-5 w-48 mb-4" />
                <div className="grid grid-cols-2 gap-6">
                  <Skeleton className="h-[180px] rounded-lg" />
                  <Skeleton className="h-[180px] rounded-lg" />
                </div>
              </Card>
            ) : null}
          </div>

          {/* ── Ranking + Itens por Ticket (1/3 width) ── */}
          <div className="flex flex-col gap-3">
            {topProdutos.length > 0 && (
              <Card variant="bordered" padding="sm">
                <SectionHeader
                  icon={BarChart3}
                  action={
                    <button
                      onClick={() => navigate('/bi/ranking')}
                      className="text-xs text-primary hover:text-primary-hover font-medium flex items-center gap-1 transition whitespace-nowrap"
                    >
                      Ver completo <ArrowRight size={12} />
                    </button>
                  }
                >
                  Top Produtos
                </SectionHeader>
                <div className="flex flex-col gap-0.5 mt-2">
                  {topProdutos.map((item, i) => (
                    <div
                      key={item.codigo}
                      onClick={() => navigate(`/bi/sku?codigo=${item.codigo}`)}
                      className="group flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-bg-hover cursor-pointer transition"
                    >
                      <span className={`
                        text-xs font-bold w-5 h-5 shrink-0 flex items-center justify-center rounded-full
                        ${i === 0 ? 'bg-primary/15 text-primary' : i === 1 ? 'bg-chart-2/15 text-chart-2' : i === 2 ? 'bg-chart-3/15 text-chart-3' : 'bg-bg-hover text-text-muted'}
                      `}>
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

            {/* ── Itens por Ticket (micro stat card) ── */}
            {kpisAtivos && (
              <Card variant="bordered" padding="sm">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[11px] font-mono font-bold uppercase tracking-widest text-text-muted">
                      Itens / Ticket
                    </p>
                    <p className="text-lg font-bold text-text-primary tabular-nums mt-1">
                      {animItensTicket.toFixed(2)}
                    </p>
                  </div>
                  {temComparativo && getVariacao('itens_por_ticket') != null && (
                    <span className={`
                      text-xs font-semibold flex items-center gap-1 px-2 py-1 rounded-full
                      ${(() => {
                        const v = getVariacao('itens_por_ticket')!
                        return v >= 0 ? 'bg-success-light text-success' : 'bg-danger-light text-danger'
                      })()}
                    `}>
                      {(() => {
                        const v = getVariacao('itens_por_ticket')!
                        return v >= 0 ? '▲' : '▼'
                      })()} {Math.abs(getVariacao('itens_por_ticket')!).toFixed(1)}%
                    </span>
                  )}
                </div>
                {temComparativo && getAnterior('itens_por_ticket') != null && (
                  <p className="text-[11px] text-text-muted mt-1.5">
                    Ano passado: <span className="font-medium text-text-secondary">{getAnterior('itens_por_ticket')!.toFixed(2)}</span>
                  </p>
                )}
              </Card>
            )}

            {/* ── Ranking skeleton ── */}
            {loading && topProdutos.length === 0 && (
              <Card variant="bordered" padding="sm">
                <Skeleton className="h-5 w-36 mb-3" />
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3 px-2 py-1.5">
                    <Skeleton className="h-4 w-5 rounded-full" />
                    <Skeleton className="h-4 flex-1" />
                    <Skeleton className="h-4 w-16" />
                  </div>
                ))}
              </Card>
            )}
          </div>
        </div>
      )}
    </BiPageLayout>
  )
}
