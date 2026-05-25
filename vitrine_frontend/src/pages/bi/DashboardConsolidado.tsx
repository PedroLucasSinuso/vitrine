import { useState, useCallback, useEffect, useRef } from 'react'
import { subDays, format } from 'date-fns'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'
import { RefreshCw, Download, TrendingUp, DollarSign, BarChart3 } from 'lucide-react'
import { fetchKpisComparativo, fetchDiario, fetchRanking, fetchCurvaAbc } from '../../api/bi'
import { exportarExcelBI } from '../../api/bi'
import type { PeriodoBi, KpisComparativoDTO, ItemRankingDTO, ItemCurvaAbcDTO, PontoDiarioDTO } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import type { Column } from '../../components/ui/DataTable'
import KpiCard from '../../components/ui/KpiCard'
import ProgressBar from '../../components/ui/ProgressBar'
import DataTable from '../../components/ui/DataTable'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import BiPageLayout from '../../components/bi/BiPageLayout'

const PRESETS = [
  { label: '7 dias', value: 7 },
  { label: '15 dias', value: 15 },
  { label: '30 dias', value: 30 },
]

function computePeriod(days: number): PeriodoBi {
  const hoje = new Date()
  return {
    data_inicio: format(subDays(hoje, days), 'yyyy-MM-dd'),
    data_fim: format(hoje, 'yyyy-MM-dd'),
  }
}

function formatDateBR(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' })
}

// Old Col — replaced by Column from DataTable
// Keeping for backward compat during migration

function trendDirection(v: number | null | undefined): 'up' | 'down' | 'flat' {
  if (v == null) return 'flat'
  if (v > 0) return 'up'
  if (v < 0) return 'down'
  return 'flat'
}

export default function DashboardConsolidado() {
  const [days, setDays] = useState(7)
  const [periodo, setPeriodo] = useState(() => computePeriod(7))

  const [kpis, setKpis] = useState<KpisComparativoDTO | null>(null)
  const [diario, setDiario] = useState<PontoDiarioDTO[]>([])
  const [ranking, setRanking] = useState<ItemRankingDTO[]>([])
  const [curvaAbc, setCurvaAbc] = useState<ItemCurvaAbcDTO[]>([])
  const [mostrarTudoAbc, setMostrarTudoAbc] = useState(false)
  const LIMITE_ABC = 8

  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState('')
  const [exporting, setExporting] = useState(false)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  const buscar = useCallback(async (p: PeriodoBi) => {
    setLoading(true)
    setErro('')
    try {
      const [k, d, r, c] = await Promise.all([
        fetchKpisComparativo(p),
        fetchDiario(p, 'receita_produto'),
        fetchRanking(p, 'receita_produto', 5),
        fetchCurvaAbc(p, 'produto'),
      ])
      if (!mountedRef.current) return
      setKpis(k)
      setDiario(d)
      setRanking(r)
      setCurvaAbc(c)
    } catch {
      if (mountedRef.current) setErro('Erro ao carregar dados do dashboard.')
    } finally {
      if (mountedRef.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    buscar(periodo)
  }, [periodo, buscar])

  const handlePeriodChange = (d: number) => {
    setDays(d)
    setPeriodo(computePeriod(d))
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      await exportarExcelBI(periodo, 'dashboard_consolidado')
    } catch {
      // silent — toast handled by api layer
    } finally {
      setExporting(false)
    }
  }

  const chartData = diario.map(p => ({
    data: formatDateBR(p.data),
    valor: p.valor,
  }))

  const varFaturamento = kpis?.faturamento_bruto?.variacao_pct
  const varTicket = kpis?.ticket_medio?.variacao_pct
  const varItensTicket = kpis?.itens_por_ticket?.variacao_pct

  const abcColumns: Column<ItemCurvaAbcDTO>[] = [
    {
      key: 'produto',
      label: 'Produto',
      render: (r) => r.produto ?? r.grupo ?? '—',
    },
    {
      key: 'receita',
      label: 'Receita',
      align: 'right',
      render: (r) => <span className="font-semibold tabular-nums">{formatCurrency(r.receita)}</span>,
    },
    {
      key: 'participacao',
      label: 'Participação',
      align: 'right',
      render: (r) => <span className="tabular-nums">{r.participacao_pct.toFixed(1)}%</span>,
    },
    {
      key: 'curva',
      label: 'Curva',
      render: (r) => (
        <Badge
          variant={r.curva === 'A' ? 'success' : r.curva === 'B' ? 'warning' : 'danger'}
          dot
          pulse={r.curva === 'A'}
        >
          {r.curva}
        </Badge>
      ),
    },
  ]

  return (
    <BiPageLayout titulo="Dashboard Consolidado" subtitulo="Visão executiva consolidada do período">

      {/* ── Period Selector + Actions ── */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Period selector as Button group */}
        <div className="flex bg-bg-card rounded-xl border border-border p-0.5 gap-0.5 shadow-sm">
          {PRESETS.map((p) => (
            <button
              key={p.value}
              onClick={() => handlePeriodChange(p.value)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all duration-fast ${
                days === p.value
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => buscar(periodo)}
          loading={loading}
          className="!p-2"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleExport}
          loading={exporting}
          className="hidden sm:inline-flex"
        >
          <Download size={14} />
          Exportar
        </Button>
      </div>

      {/* ── Error banner ── */}
      {erro && (
        <div className="bg-danger-light border border-danger/20 rounded-xl px-4 py-3 text-sm font-medium text-danger flex items-center gap-2" role="alert">
          <span className="w-1.5 h-1.5 rounded-full bg-danger shrink-0" />
          {erro}
        </div>
      )}

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="animate-fade-in-up" style={{ animationDelay: '0ms' }}>
          <KpiCard
            label="Faturamento Bruto"
            value={formatCurrency(kpis?.faturamento_bruto?.atual ?? 0)}
            trend={varFaturamento != null ? {
              value: `${Math.abs(varFaturamento).toFixed(1)}%`,
              direction: trendDirection(varFaturamento),
            } : undefined}
            icon={<DollarSign size={16} />}
          />
        </div>
        <div className="animate-fade-in-up" style={{ animationDelay: '100ms' }}>
          <KpiCard
            label="Ticket Médio"
            value={formatCurrency(kpis?.ticket_medio?.atual ?? 0)}
            trend={varTicket != null ? {
              value: `${Math.abs(varTicket).toFixed(1)}%`,
              direction: trendDirection(varTicket),
            } : undefined}
            icon={<TrendingUp size={16} />}
          />
        </div>
        <div className="animate-fade-in-up" style={{ animationDelay: '200ms' }}>
          <KpiCard
            label="Itens por Ticket"
            value={(kpis?.itens_por_ticket?.atual ?? 0).toFixed(2)}
            trend={varItensTicket != null ? {
              value: `${Math.abs(varItensTicket).toFixed(1)}%`,
              direction: trendDirection(varItensTicket),
            } : undefined}
            icon={<BarChart3 size={16} />}
          />
        </div>
      </div>

      {/* ── Chart + Ranking grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Revenue chart */}
        <Card variant="default" className="lg:col-span-2 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary font-display flex items-center gap-2">
              <TrendingUp size={16} className="text-primary" />
              Receita Diária
            </h2>
            {loading && <RefreshCw size={14} className="animate-spin text-text-muted" />}
          </div>
          {chartData.length > 0 ? (
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="receitaGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--color-primary)" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="var(--color-primary)" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="data"
                    tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
                    axisLine={false}
                    tickLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
                    axisLine={false}
                    tickLine={false}
                    width={55}
                    tickFormatter={(v: number) => `R$${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--color-surface-modal)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 8,
                      fontSize: 12,
                      color: 'var(--color-text-primary)',
                      boxShadow: 'var(--shadow-card)',
                    }}
                    formatter={(value) => [formatCurrency(Number(value ?? 0)), 'Receita']}
                    labelStyle={{ color: 'var(--color-text-muted)' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="valor"
                    stroke="var(--color-primary)"
                    strokeWidth={2.5}
                    fill="url(#receitaGrad)"
                    animationDuration={800}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[220px]">
              {loading ? <Skeleton variant="chart" className="h-full" /> : (
                <div className="h-full flex items-center justify-center text-sm text-text-muted">Nenhum dado disponível</div>
              )}
            </div>
          )}
        </Card>

        {/* Top 5 ranking */}
        <Card variant="default" className="p-5">
          <h2 className="text-sm font-semibold text-text-primary font-display flex items-center gap-2 mb-4">
            <BarChart3 size={16} className="text-primary" />
            Top 5 Produtos
          </h2>
          {ranking.length > 0 ? (
            <div className="flex flex-col gap-3">
              {ranking.map((item, idx) => {
                const maxValor = ranking[0]?.valor ?? 1
                const rankColors = [
                  'bg-accent text-white',           // #1 gold
                  'bg-text-muted text-bg-sidebar',   // #2 silver
                  'bg-danger text-white',            // #3 bronze
                  'bg-bg-card text-text-muted',       // #4+
                  'bg-bg-card text-text-muted',
                ]
                return (
                  <div key={item.codigo}>
                    <div className="flex justify-between items-center mb-1.5">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 ${rankColors[idx] || rankColors[3]}`}>
                          {idx + 1}
                        </span>
                        <span className="text-sm text-text-primary truncate">{item.produto}</span>
                      </div>
                      <div className="text-right shrink-0 ml-2">
                        <span className="text-xs font-bold text-text-primary tabular-nums">{formatCurrency(item.valor)}</span>
                      </div>
                    </div>
                    <ProgressBar
                      value={item.valor}
                      max={maxValor}
                      variant={idx === 0 ? 'warning' : idx === 1 ? 'primary' : idx === 2 ? 'danger' : 'primary'}
                      size="sm"
                    />
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="h-[180px]">
              {loading ? (
                <div className="flex flex-col gap-3 p-2">
                  {[1,2,3,4,5].map(i => (
                    <div key={i} className="flex items-center gap-2">
                      <Skeleton className="w-6 h-6 rounded-full shrink-0" />
                      <Skeleton className="h-4 flex-1" />
                      <Skeleton className="w-16 h-4 rounded-md" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-sm text-text-muted">Nenhum dado</div>
              )}
            </div>
          )}
        </Card>
      </div>

      {/* ── ABC Curve Table ── */}
      <Card variant="default" className="p-5">
        <h2 className="text-sm font-semibold text-text-primary font-display flex items-center gap-2 mb-4">
          <DollarSign size={16} className="text-primary" />
          Curva ABC
        </h2>
        {curvaAbc.length > 0 ? (
          <>
            <DataTable
              columns={abcColumns}
              data={mostrarTudoAbc ? curvaAbc : curvaAbc.slice(0, LIMITE_ABC)}
              rowKey={(r) => r.produto ?? r.grupo ?? ''}
            />
            {curvaAbc.length > LIMITE_ABC && (
              <button
                onClick={() => setMostrarTudoAbc(!mostrarTudoAbc)}
                className="mt-3 text-xs font-semibold text-primary hover:text-primary/80 transition mx-auto block"
              >
                {mostrarTudoAbc
                  ? 'Mostrar menos'
                  : `Ver mais ${curvaAbc.length - LIMITE_ABC} itens`
                }
              </button>
            )}
          </>
        ) : (
          <div className="h-[120px]">
            {loading ? (
              <div className="flex flex-col gap-3 p-2">
                {[1,2,3,4].map(i => (
                  <div key={i} className="flex items-center gap-4">
                    <Skeleton className="h-4 flex-1" />
                    <Skeleton className="w-20 h-4 rounded-md" />
                    <Skeleton className="w-12 h-4 rounded-md" />
                    <Skeleton className="w-10 h-6 rounded-full" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-text-muted">Nenhum dado disponível</div>
            )}
          </div>
        )}
      </Card>

      {/* ── Mobile Export ── */}
      <div className="sm:hidden flex justify-center">
        <Button onClick={handleExport} loading={exporting} fullWidth>
          <Download size={14} />
          Exportar
        </Button>
      </div>

    </BiPageLayout>
  )
}
