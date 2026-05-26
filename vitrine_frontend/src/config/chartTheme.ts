type AxisStyle = {
  tick: { fontSize: number; fill: string }
  axisLine: { stroke: string } | boolean
  tickLine: boolean
  angle?: number
  textAnchor?: 'inherit' | 'end' | 'middle' | 'start'
  height?: number
  interval?: 'preserveStartEnd'
  minTickGap?: number
}

type TooltipStyle = {
  cursor: { fill: string }
  contentStyle: React.CSSProperties
}

export interface ChartTheme {
  margin: { top: number; right: number; bottom: number; left: number }
  xAxis: AxisStyle
  yAxis: AxisStyle
  tooltip: TooltipStyle
  area: { fillOpacity: number; strokeWidth: number }
  line: { strokeWidth: number; dot: boolean; activeDot: { r: number } }
}

export const CHART_THEME: ChartTheme = {
  margin: { top: 8, right: 8, bottom: 4, left: 4 },

  xAxis: {
    tick: { fontSize: 11, fill: 'var(--color-text-muted)' },
    axisLine: { stroke: 'var(--color-border)' },
    tickLine: false,
    angle: -30,
    textAnchor: 'end',
    height: 60,
    interval: 'preserveStartEnd',
    minTickGap: 40,
  },

  yAxis: {
    tick: { fontSize: 11, fill: 'var(--color-text-muted)' },
    axisLine: false,
    tickLine: false,
  },

  tooltip: {
    cursor: { fill: 'rgba(100,100,100,0.06)' },
    contentStyle: {
      background: 'var(--color-bg-card)',
      border: '1px solid var(--color-border)',
      borderRadius: 8,
      boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      fontSize: 12,
    },
  },

  area: {
    fillOpacity: 0.15,
    strokeWidth: 2,
  },

  line: {
    strokeWidth: 2,
    dot: false,
    activeDot: { r: 4 },
  },
}

/** Helper to format currency on chart axes */
export function formatChartCurrency(value: number): string {
  if (value >= 1_000_000) return `R$ ${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `R$ ${(value / 1_000).toFixed(0)}k`
  return `R$ ${value.toFixed(0)}`
}

/** Helper to format plain numbers on chart axes */
export function formatChartNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}k`
  return value.toFixed(0)
}
