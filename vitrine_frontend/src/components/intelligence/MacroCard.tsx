/** Card individual de indicador macroeconômico com estado disponível/indisponível. */
import { TrendingUp, TrendingDown, Minus, AlertCircle, HelpCircle } from 'lucide-react'
import type { MacroIndicator } from '../../types/macro'

interface Props {
  indicador: MacroIndicator
}

function formatarData(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso
  }
}

export default function MacroCard({ indicador }: Props) {
  if (!indicador.disponivel) {
    return (
      <div className="shrink-0 w-[170px] bg-danger/[0.06] rounded-xl border border-danger/20 p-3 text-center">
        {/* Rótulo */}
        <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider block mb-1">
          {indicador.rotulo}
        </span>

        {/* Estado indisponível */}
        <div className="flex items-center justify-center gap-1.5 mb-2" title={indicador.mensagem || undefined}>
          <AlertCircle size={14} className="text-danger shrink-0" />
          <span className="text-xs font-medium text-danger">API indisponível</span>
        </div>

        {/* Timestamp */}
        <span className="text-[9px] text-text-muted block leading-tight">
          Falha em: {formatarData(indicador.consultado_em)}
        </span>
      </div>
    )
  }

  // Determinar direção da tendência baseado no valor vs. referência
  // Indicadores > 5% são "altos" (exceto desemprego que > 12% é alto)
  const isElevado = indicador.valor !== null && (
    indicador.chave.startsWith('selic') ? indicador.valor > 10 :
    indicador.chave === 'desemprego' ? indicador.valor > 12 :
    indicador.valor > 5
  )

  const TrendIcon = isElevado ? TrendingUp : (indicador.valor !== null && indicador.valor < 2 ? TrendingDown : Minus)
  const trendColor = isElevado ? 'text-danger' : (indicador.valor !== null && indicador.valor < 2 ? 'text-success' : 'text-text-muted')

  return (
    <div className="shrink-0 w-[170px] bg-bg-card rounded-xl border border-border/40 p-3 hover:border-border/70 transition-colors text-center">
      {/* Rótulo */}
      <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider block mb-1">
        {indicador.rotulo}
      </span>

      {/* Valor + tendência */}
      <div className="flex items-center justify-center gap-1.5 mb-0.5">
        <span className="text-lg font-bold text-text-primary font-display tracking-tight">
          {indicador.valor?.toFixed(2).replace('.', ',')}
          <span className="text-xs font-medium text-text-muted ml-0.5">{indicador.unidade}</span>
        </span>
        <TrendIcon size={14} className={trendColor} />
      </div>

      {/* Período de referência */}
      {indicador.periodo_ref && (
        <span className="text-[10px] text-text-muted block">
          {indicador.periodo_ref}
        </span>
      )}

      {/* Timestamp de consulta */}
      <div className="flex items-center justify-center gap-1 mt-1.5 pt-1.5 border-t border-border/20">
        <HelpCircle size={8} className="text-text-muted" />
        <span className="text-[8px] text-text-muted">
          {formatarData(indicador.consultado_em)}
        </span>
      </div>
    </div>
  )
}
