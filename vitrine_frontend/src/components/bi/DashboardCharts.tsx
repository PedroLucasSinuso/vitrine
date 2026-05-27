import { memo } from 'react'
import { format } from 'date-fns'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import { TrendingUp, Clock4 } from 'lucide-react'
import Card from '../ui/Card'
import SectionHeader from '../ui/SectionHeader'
import Skeleton from '../ui/Skeleton'
import { formatCurrency } from '../../utils/formatters'
import { CHART_THEME, formatChartCurrency, formatChartNumber } from '../../config/chartTheme'
import type { PontoDiarioDTO, PontoHoraDTO } from '../../types'

interface DashboardChartsProps {
  diarioTicketMedio: PontoDiarioDTO[]
  diarioTickets: PontoDiarioDTO[]
  dadosHora: PontoHoraDTO[]
  loadingDiario: boolean
  loadingHora: boolean
}

function formatDateTick(value: string): string {
  const d = new Date(value + 'T00:00:00')
  return format(d, 'dd/MM')
}

export default memo(function DashboardCharts({
  diarioTicketMedio, diarioTickets, dadosHora,
  loadingDiario, loadingHora,
}: DashboardChartsProps) {
  const temGraficos = diarioTicketMedio.length > 1 || diarioTickets.length > 1
  const temDadosHora = dadosHora.length > 0

  if (!temGraficos && !loadingDiario && !temDadosHora && !loadingHora) return null

  return (
    <div className="flex flex-col gap-5">
      {/* ── Tendências (Ticket Médio + Tickets lado a lado) ── */}
      {temGraficos ? (
        <Card variant="bordered" padding="md">
          <SectionHeader icon={TrendingUp}>Tendências no Período</SectionHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
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

      {/* ── Receita por Hora (full-width abaixo das tendências) ── */}
      {temDadosHora ? (
        <Card variant="bordered" padding="md">
          <SectionHeader icon={Clock4}>Receita por Hora</SectionHeader>
          <div className="mt-3">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={dadosHora}
                layout="vertical"
                margin={{ top: 2, right: 16, left: 28, bottom: 2 }}
                barCategoryGap={2}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--color-border)" />
                <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
                <YAxis dataKey="hora" type="category" tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} width={28} />
                <Tooltip
                  cursor={{ fill: 'rgba(100,100,100,0.06)' }}
                  contentStyle={CHART_THEME.tooltip.contentStyle}
                  formatter={((v: number) => formatCurrency(v)) as never}
                />
                <Bar dataKey="valor" fill="var(--color-primary)" radius={[0, 4, 4, 0]} maxBarSize={14} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      ) : loadingHora ? (
        <Card variant="bordered" padding="md">
          <Skeleton className="h-5 w-36 mb-4" />
          <Skeleton className="h-[260px] rounded-lg" />
        </Card>
      ) : null}
    </div>
  )
})
