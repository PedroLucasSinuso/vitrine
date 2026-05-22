import { useState, useRef, useEffect } from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface VariacaoInfo {
  valor: number
  direcao: 'positivo' | 'negativo' | 'estavel'
}

interface Props {
  label: string
  valor: string
  pulseKey?: number
  variacao?: VariacaoInfo | null
  valorAnterior?: string
}

export default function HeroKpiCard({ label, valor, pulseKey, variacao, valorAnterior }: Props) {
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

  const varColor = variacao
    ? variacao.direcao === 'positivo' ? 'text-success'
      : variacao.direcao === 'negativo' ? 'text-danger' : 'text-text-muted'
    : ''

  const VarIcon = variacao
    ? variacao.direcao === 'positivo' ? TrendingUp
      : variacao.direcao === 'negativo' ? TrendingDown : Minus
    : Minus

  return (
    <div
      className={`relative overflow-hidden bg-gradient-to-br from-primary/5 via-bg-card to-primary/[0.08] rounded-2xl shadow-sm border border-primary/10 p-6 md:p-8 animate-scale-in ${pulsing ? 'animate-pulse-glow' : ''}`}
    >
      <div className="absolute top-0 right-0 w-48 h-48 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
      <p className="text-xs font-semibold text-text-muted mb-2">{label}</p>
      <p className="text-2xl md:text-4xl font-bold text-text-primary mb-3">
        {valor}
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
