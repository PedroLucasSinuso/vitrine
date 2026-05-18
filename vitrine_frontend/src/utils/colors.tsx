/**
 * Shared color constants for data visualisation.
 * Charts use these hex values in Recharts `<defs>` and `<Cell>` fills
 * because SVG gradients cannot reference Tailwind CSS variables directly.
 */
/* eslint-disable react-refresh/only-export-components */
import type { ReactNode } from 'react'

export const CHART = {
  green: '#059669',
  amber: '#f59e0b',
  indigo: '#6366f1',
  cyan: '#06b6d4',
  gray: '#6b7280',
  blue: '#3b82f6',
  red: '#ef4444',
} as const

export const CURVA_CORES = {
  A: CHART.green,
  B: CHART.amber,
  C: CHART.gray,
} as const

/**
 * Reusable SVG linear gradient component for Recharts.
 *
 * Usage:
 *   <ChartGradient id="myGradient" color={CHART.green} />
 *   <Bar dataKey="valor" fill="url(#myGradient)" />
 */
export function ChartGradient({
  id,
  color = CHART.green,
  x1 = 0,
  y1 = 0,
  x2 = 0,
  y2 = 1,
}: {
  id: string
  color?: string
  x1?: number
  y1?: number
  x2?: number
  y2?: number
}) {
  return (
    <linearGradient id={id} x1={x1} y1={y1} x2={x2} y2={y2}>
      <stop offset="0%" stopColor={color} stopOpacity={0.9} />
      <stop offset="100%" stopColor={color} stopOpacity={0.25} />
    </linearGradient>
  )
}

/**
 * Build a <defs> wrapper around one or more gradients.
 *
 * Usage:
 *   <ChartDefs>
 *     <ChartGradient id="g1" color={CHART.green} />
 *     <ChartGradient id="g2" color={CHART.amber} />
 *   </ChartDefs>
 */
export function ChartDefs({ children }: { children: ReactNode }) {
  return <defs>{children}</defs>
}
