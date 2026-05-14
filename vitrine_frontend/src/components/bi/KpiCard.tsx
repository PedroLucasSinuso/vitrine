import { useState, useEffect } from 'react'

interface VariacaoInfo {
  valor: number
  direcao: 'positivo' | 'negativo' | 'estavel'
}

interface Props {
  label: string
  valor: string
  destaque?: boolean
  delay?: number
  pulseKey?: number
  variacao?: VariacaoInfo | null
  invertVariation?: boolean
}

export default function KpiCard({ label, valor, destaque, delay = 0, pulseKey, variacao, invertVariation }: Props) {
  const [pulsing, setPulsing] = useState(false)

  useEffect(() => {
    if (pulseKey === undefined) return
    setPulsing(true)
    const t = setTimeout(() => setPulsing(false), 800)
    return () => clearTimeout(t)
  }, [pulseKey])

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-1 animate-fade-in-up ${pulsing ? 'animate-pulse-glow' : ''}`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`font-bold break-words ${destaque ? 'text-xl md:text-3xl text-primary dark:text-primary-light' : 'text-base md:text-xl text-gray-800 dark:text-gray-100'}`}>
        {valor}
        {variacao && (
          <span
            className={`inline-flex items-center gap-0.5 text-sm ml-2 font-semibold ${
              invertVariation
                ? variacao.direcao === 'negativo' ? 'text-green-600' :
                  variacao.direcao === 'positivo' ? 'text-red-600' : 'text-gray-400'
                : variacao.direcao === 'positivo' ? 'text-green-600' :
                  variacao.direcao === 'negativo' ? 'text-red-600' : 'text-gray-400'
            }`}
          >
            {variacao.direcao === 'positivo' ? '▲' : variacao.direcao === 'negativo' ? '▼' : '◆'}
            {Math.abs(variacao.valor).toFixed(1)}%
          </span>
        )}
      </p>
    </div>
  )
}