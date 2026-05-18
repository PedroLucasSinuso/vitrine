import type { ReactNode } from 'react'
import { formatCurrency } from '../../utils/formatters'

interface TooltipPayload {
  value: number
}

interface Props {
  active?: boolean
  payload?: TooltipPayload[]
  label?: string
  labelPrefix?: string
  formatValue?: (v: number) => string
  children?: ReactNode
}

export default function BiTooltip({ active, payload, label, labelPrefix = '', formatValue = formatCurrency }: Props) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-900 text-white px-3 py-2 rounded-lg shadow-lg text-xs">
      {label && <p className="font-semibold mb-1">{labelPrefix}{label}</p>}
      <p>{formatValue(payload[0].value)}</p>
    </div>
  )
}
