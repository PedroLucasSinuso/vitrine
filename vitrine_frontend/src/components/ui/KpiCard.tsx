import type { ReactNode } from 'react'
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react'

interface Props {
  label: string
  value: string
  trend?: {
    value: string
    direction: 'up' | 'down' | 'flat'
    label?: string
  }
  icon?: ReactNode
  className?: string
}

export default function KpiCard({ label, value, trend, icon, className = '' }: Props) {
  return (
    <div className={`bg-bg-card border border-border rounded-xl p-6 transition-all hover:border-border-light ${className}`}>
      <div className="flex justify-between items-start mb-4">
        <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-text-muted">
          {label}
        </span>
        {icon && (
          <div className="p-2 bg-primary-light text-primary rounded-lg">
            {icon}
          </div>
        )}
      </div>
      <div className="space-y-1">
        <h3 className="text-2xl font-black font-display text-text-primary">
          {value}
        </h3>
        {trend && (
          <div className="flex items-center gap-1.5 pt-1">
            <span
              className={`inline-flex items-center gap-0.5 text-[11px] font-bold px-1.5 py-0.5 rounded-full border ${
                trend.direction === 'up'
                  ? 'bg-success-light text-success border-success/20'
                  : trend.direction === 'down'
                  ? 'bg-danger-light text-danger border-danger/20'
                  : 'bg-warning-light text-warning border-warning/20'
              }`}
            >
              {trend.direction === 'up' ? (
                <ArrowUpRight size={12} />
              ) : trend.direction === 'down' ? (
                <ArrowDownRight size={12} />
              ) : (
                <Minus size={12} />
              )}
              {trend.value}
            </span>
            {trend.label && (
              <span className="text-[10px] text-text-muted font-medium">{trend.label}</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
