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
  const pulseTimer = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    if (pulseKey === undefined) return
    if (pulseTimer.current) clearTimeout(pulseTimer.current)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPulsing(true)
    pulseTimer.current = setTimeout(() => setPulsing(false), 800)
    return () => { if (pulseTimer.current) clearTimeout(pulseTimer.current) }
  }, [pulseKey])

  const varColor = variacao
    ? variacao.direcao === 'positivo' ? 'text-green-600 dark:text-green-400'
      : variacao.direcao === 'negativo' ? 'text-red-600 dark:text-red-400' : 'text-slate-400'
    : ''

  const VarIcon = variacao
    ? variacao.direcao === 'positivo' ? TrendingUp
      : variacao.direcao === 'negativo' ? TrendingDown : Minus
    : Minus

  return (
    <div
      className={`relative overflow-hidden bg-gradient-to-br from-primary/5 via-white to-primary/[0.08] dark:from-primary/10 dark:via-slate-800 dark:to-primary/[0.05] rounded-2xl shadow-sm border border-primary/10 dark:border-primary/20 p-6 md:p-8 animate-scale-in ${pulsing ? 'animate-pulse-glow' : ''}`}
    >
      <div className="absolute top-0 right-0 w-48 h-48 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">{label}</p>
      <p className="text-2xl md:text-4xl font-bold text-slate-900 dark:text-white mb-3">
        {valor}
      </p>
      <div className="flex items-center gap-4 flex-wrap">
        {variacao && (
          <span className={`flex items-center gap-1.5 text-sm font-semibold ${varColor}`}>
            <VarIcon size={16} strokeWidth={2.5} />
            {Math.abs(variacao.valor).toFixed(1)}%
            <span className="text-slate-400 font-normal text-xs">vs ano anterior</span>
          </span>
        )}
        {valorAnterior && (
          <span className="text-xs text-slate-400 dark:text-slate-500">
            Ano passado: <span className="font-medium text-slate-600 dark:text-slate-300">{valorAnterior}</span>
          </span>
        )}
      </div>
    </div>
  )
}
