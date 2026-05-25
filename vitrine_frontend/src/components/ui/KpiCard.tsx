import { useState, useRef, useEffect, type ReactNode } from 'react'
import { ArrowUpRight, ArrowDownRight, Minus, TrendingUp, TrendingDown } from 'lucide-react'

interface VariacaoInfo {
  valor: number
  direcao: 'positivo' | 'negativo' | 'estavel'
}

interface Props {
  label: string
  value?: string
  valor?: string
  trend?: {
    value: string
    direction: 'up' | 'down' | 'flat'
    label?: string
  }
  icon?: ReactNode
  className?: string
  delay?: number
  pulseKey?: number
  hero?: boolean
  variacao?: VariacaoInfo | null
  invertVariation?: boolean
  valorAnterior?: string
}

export default function KpiCard({
  label,
  value,
  valor,
  trend,
  icon,
  className = '',
  delay = 0,
  pulseKey,
  hero = false,
  variacao,
  invertVariation,
  valorAnterior,
}: Props) {
  const [pulsing, setPulsing] = useState(false)
  const pulseTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (pulseKey === undefined) return
    if (pulseTimer.current) clearTimeout(pulseTimer.current)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPulsing(true)
    pulseTimer.current = setTimeout(() => setPulsing(false), 800)
    return () => { if (pulseTimer.current) clearTimeout(pulseTimer.current) }
  }, [pulseKey])

  const displayValue = valor ?? value ?? ''

  const varColor = variacao
    ? invertVariation
      ? variacao.direcao === 'negativo' ? 'text-success'
        : variacao.direcao === 'positivo' ? 'text-danger' : 'text-text-muted'
      : variacao.direcao === 'positivo' ? 'text-success'
        : variacao.direcao === 'negativo' ? 'text-danger' : 'text-text-muted'
    : ''

  const VarIcon = variacao
    ? variacao.direcao === 'positivo' ? TrendingUp
      : variacao.direcao === 'negativo' ? TrendingDown : Minus
    : Minus

  if (hero) {
    return (
      <div
        className={`relative overflow-hidden bg-gradient-to-br from-primary/5 via-bg-card to-primary/[0.08] rounded-2xl shadow-sm border border-primary/10 p-6 md:p-8 animate-scale-in ${pulsing ? 'animate-pulse-glow' : ''} ${className}`}
        style={{ animationDelay: `${delay}ms` }}
      >
        <div className="absolute top-0 right-0 w-48 h-48 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
        <p className="text-xs font-semibold text-text-muted mb-2">{label}</p>
        <p className="text-2xl md:text-4xl font-bold text-text-primary mb-3">
          {displayValue}
        </p>
        <div className="flex items-center gap-4 flex-wrap">
          {variacao && (
            <span className={`flex items-center gap-1.5 text-sm font-semibold ${varColor}`}>
              <VarIcon size={16} strokeWidth={2.5} />
              {Math.abs(variacao.valor).toFixed(1)}%
              <span className="text-text-muted font-normal text-xs">vs ano anterior</span>
            </span>
          )}
          {valorAnterior && (
            <span className="text-xs text-text-muted">
              Ano passado: <span className="font-medium text-text-secondary">{valorAnterior}</span>
            </span>
          )}
        </div>
      </div>
    )
  }

  return (
    <div
      className={`relative bg-bg-card border border-border rounded-xl p-6 transition-all duration-fast hover:shadow-card-hover hover:-translate-y-0.5 overflow-hidden animate-fade-in-up ${pulsing ? 'animate-pulse-glow' : ''} ${className}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="absolute inset-x-0 top-0 h-0.5 bg-primary rounded-t-xl" />
      <div className="flex justify-between items-start mb-4">
        <span className="text-[11px] font-mono font-bold uppercase tracking-widest text-text-muted">
          {label}
        </span>
        {icon && (
          <div className="p-2 bg-primary-light text-primary rounded-lg">
            {icon}
          </div>
        )}
      </div>
      <div className="space-y-1">
        <h3 className="text-2xl font-black font-display text-text-primary tabular-nums tracking-tight">
          {displayValue}
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
        {!trend && variacao && (
          <span className={`flex items-center gap-1 text-xs font-semibold ${varColor}`}>
            <VarIcon size={12} strokeWidth={2.5} />
            {Math.abs(variacao.valor).toFixed(1)}%
          </span>
        )}
        {!trend && !variacao && valorAnterior && (
          <span className="text-xs text-text-muted block pt-1">
            Ano passado: <span className="font-medium text-text-secondary">{valorAnterior}</span>
          </span>
        )}
      </div>
    </div>
  )
}
