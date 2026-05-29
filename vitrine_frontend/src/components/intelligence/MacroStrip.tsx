/** Strip horizontal de indicadores macroeconômicos. */
import { AlertCircle, BarChart3 } from 'lucide-react'
import Skeleton from '../ui/Skeleton'
import MacroCard from './MacroCard'
import type { MacroIndicator } from '../../types/macro'

interface Props {
  indicadores: MacroIndicator[]
  loading: boolean
  erro: string | null
}

export default function MacroStrip({ indicadores, loading, erro }: Props) {
  // Loading: skeleton shimmer
  if (loading) {
    return (
      <div className="flex gap-3 overflow-x-auto pb-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-[98px] w-[170px] shrink-0 rounded-xl" />
        ))}
      </div>
    )
  }

  // Erro: banner silencioso (não crítico — indicadores são complementares)
  if (erro) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-warning/[0.06] border border-warning/20 text-[11px] text-warning">
        <AlertCircle size={12} />
        <span>Indicadores macroeconômicos temporariamente indisponíveis</span>
      </div>
    )
  }

  // Empty: esconder (sem indicadores configurados)
  if (indicadores.length === 0) {
    return null
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-2 mb-2.5">
        <BarChart3 size={14} className="text-text-muted" />
        <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
          Contexto Macroeconômico
        </span>
        <span className="text-[9px] text-text-muted bg-bg-hover/50 px-1.5 py-0.5 rounded-full">
          {indicadores.filter(i => i.disponivel).length}/{indicadores.length} disponíveis
        </span>
      </div>

      {/* Strip com scroll horizontal */}
      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin snap-x snap-mandatory -mx-1 px-1 scroll-smooth">
        {indicadores.map(ind => (
          <MacroCard key={ind.chave} indicador={ind} />
        ))}
      </div>
    </div>
  )
}
