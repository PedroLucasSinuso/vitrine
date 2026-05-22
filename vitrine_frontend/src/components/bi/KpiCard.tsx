import { useState, useRef, useEffect } from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface VariacaoInfo {
  valor: number
  direcao: 'positivo' | 'negativo' | 'estavel'
}

interface Props {
  label: string
  valor: string
  delay?: number
  pulseKey?: number
  variacao?: VariacaoInfo | null
  invertVariation?: boolean
  valorAnterior?: string
}

export default function KpiCard({ label, valor, delay = 0, pulseKey, variacao, invertVariation, valorAnterior }: Props) {
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

  return (
    <div
      className={`bg-bg-card border border-border rounded-xl p-4 md:p-5 flex flex-col animate-fade-in-up ${pulsing ? 'animate-pulse-glow' : ''}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <p className="text-xs text-text-muted font-medium mb-1.5">{label}</p>
      <p className="text-base md:text-xl font-bold text-text-primary break-words mb-2">
        {valor}
      </p>
      {variacao && (
        <span className={`flex items-center gap-1 text-xs font-semibold ${varColor}`}>
          <VarIcon size={12} strokeWidth={2.5} />
          {Math.abs(variacao.valor).toFixed(1)}%
        </span>
      )}
      {valorAnterior && !variacao && (
          <span className="text-xs text-text-muted mt-auto">
            Ano passado: <span className="font-medium text-text-secondary">{valorAnterior}</span>
        </span>
      )}
    </div>
  )
}
