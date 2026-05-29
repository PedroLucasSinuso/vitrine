/** Card de insight premium com semântica visual, glow contextual e microinterações. */
import { useState } from 'react'
import {
  Lightbulb, X, AlertTriangle, RefreshCw,
  ShoppingCart, Calendar, List, ChevronRight,
  Sparkles, TrendingDown, BarChart3,
} from 'lucide-react'
import Badge from '../ui/Badge'
import Button from '../ui/Button'
import ProductListModal from './ProductListModal'
import type { Insight, InsightTipo, Impacto } from '../../types/intelligence'

const TIPO_ICON: Record<InsightTipo, React.ReactNode> = {
  encalhe: <AlertTriangle size={16} />,
  margem_erosao: <TrendingDown size={16} />,
  taxa_troca: <RefreshCw size={16} />,
  oportunidade_b: <Lightbulb size={16} />,
  sazonalidade: <Calendar size={16} />,
  macro_contexto: <BarChart3 size={16} />,
  outro: <ShoppingCart size={16} />,
}

const IMPACTO_CONFIG: Record<Impacto, {
  border: string
  glow: string
  badge: 'danger' | 'warning' | 'info'
  label: string
  gradient: string
}> = {
  alto: {
    border: 'border-l-[3px] border-l-danger',
    glow: 'hover:shadow-[0_0_20px_color-mix(in_srgb,var(--color-danger),10%)]',
    badge: 'danger',
    label: 'ALTO',
    gradient: 'from-danger/[0.03] to-transparent',
  },
  medio: {
    border: 'border-l-[3px] border-l-warning',
    glow: 'hover:shadow-[0_0_20px_color-mix(in_srgb,var(--color-warning),8%)]',
    badge: 'warning',
    label: 'MÉDIO',
    gradient: 'from-warning/[0.03] to-transparent',
  },
  baixo: {
    border: 'border-l-[3px] border-l-info',
    glow: 'hover:shadow-[0_0_20px_color-mix(in_srgb,var(--color-info),6%)]',
    badge: 'info',
    label: 'BAIXO',
    gradient: 'from-info/[0.03] to-transparent',
  },
}

/** Extrai primeiro valor monetário do texto */
function extractHighlight(text: string): string | null {
  const match = text.match(/[R]\$[\s]*[\d.,]+/)
  return match?.[0] ?? null
}

interface Props {
  insight: Insight
  onDismiss: () => void
}

export default function InsightCard({ insight, onDismiss }: Props) {
  const [showProdutos, setShowProdutos] = useState(false)
  const config = IMPACTO_CONFIG[insight.impacto] ?? IMPACTO_CONFIG.baixo
  const icon = TIPO_ICON[insight.tipo] ?? TIPO_ICON.outro
  const highlight = extractHighlight(insight.descricao)

  return (
    <div
      className={`
        relative group bg-bg-card rounded-xl border border-border/50
        ${config.border} ${config.glow}
        transition-all duration-300 ease-out
        hover:border-border/80 hover:-translate-y-0.5
        overflow-hidden
      `}
    >
      {/* Gradiente sutil de fundo no hover */}
      <div className={`absolute inset-0 bg-gradient-to-br ${config.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none`} />

      <div className="relative p-4 sm:p-5">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2 sm:gap-3 mb-3">
          <div className="flex items-center gap-2 sm:gap-2.5 min-w-0">
            {/* Ícone do tipo */}
            <div className={`
              p-1.5 sm:p-2 rounded-lg shrink-0
              ${insight.impacto === 'alto' ? 'bg-danger/[0.1] text-danger' : ''}
              ${insight.impacto === 'medio' ? 'bg-warning/[0.1] text-warning' : ''}
              ${insight.impacto === 'baixo' ? 'bg-info/[0.1] text-info' : ''}
            `}>
              {icon}
            </div>

            <div className="min-w-0">
              {/* Categoria + impacto + confiança */}
              <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap mb-1">
                <Badge variant={config.badge}>{config.label}</Badge>
                <span className="text-[9px] sm:text-[10px] text-text-muted uppercase font-mono tracking-wider">
                  {insight.tipo.replace(/_/g, ' ')}
                </span>
                {insight.confianca === 'hipotese' && (
                  <span className="text-[9px] sm:text-[10px] text-warning bg-warning/[0.08] px-1.5 py-0.5 rounded-full font-medium inline-flex items-center gap-1">
                    <Sparkles size={9} />
                    Hipótese
                  </span>
                )}
                {insight.confianca === 'alta' && (
                  <span className="text-[9px] sm:text-[10px] text-success bg-success/[0.08] px-1.5 py-0.5 rounded-full font-medium">
                    Confiança alta
                  </span>
                )}
              </div>

              {/* Título */}
              <h3 className="text-sm font-semibold text-text-primary leading-snug">
                {insight.titulo}
              </h3>
            </div>
          </div>

          {/* Dismiss */}
          <button
            onClick={onDismiss}
            className="p-1 rounded-md text-text-muted hover:text-danger hover:bg-danger/[0.08] transition shrink-0 -mr-1 -mt-1"
            aria-label="Ignorar insight"
          >
            <X size={14} />
          </button>
        </div>

        {/* Descrição com destaque financeiro */}
        <p className="text-xs text-text-secondary leading-relaxed mb-3">
          {insight.descricao}
          {highlight && (
            <span className="inline-block ml-1.5 px-1.5 py-0.5 rounded text-[11px] font-semibold bg-danger/[0.08] text-danger">
              {highlight}
            </span>
          )}
        </p>

        {/* Sugestão / recomendação */}
        <p className="text-xs text-text-muted italic border-l-2 border-border/50 pl-3 mb-4 leading-relaxed">
          {insight.sugestao}
        </p>

        {/* Macro: indicador de referência */}
        {insight.tipo === 'macro_contexto' && insight.metricas?.valor_indicador != null && (
          <div className="flex items-center gap-2 mb-3 text-[11px] text-text-muted bg-info/[0.06] rounded-lg px-3 py-1.5 border border-info/10">
            <BarChart3 size={12} className="text-info" />
            <span>
              Indicador de referência: <strong className="text-text-primary">{insight.metricas.valor_indicador.toFixed(2).replace('.', ',')}%</strong>
              {insight.metricas.chave_indicador && (
                <span className="ml-1 text-[10px]">({insight.metricas.chave_indicador})</span>
              )}
            </span>
          </div>
        )}

        {/* Footer actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 sm:gap-3 pt-2 border-t border-border/20">
          <div className="flex items-center gap-2 flex-wrap">
            {/* Ver produtos */}
            {insight.produtos && insight.produtos.length > 0 && (
              <button
                onClick={() => setShowProdutos(true)}
                className="inline-flex items-center gap-1 text-[11px] sm:text-xs font-medium text-text-muted hover:text-primary transition-colors group/btn"
              >
                <List size={12} />
                <span>Ver {insight.produtos.length} produtos</span>
                <ChevronRight size={12} className="group-hover/btn:translate-x-0.5 transition-transform" />
              </button>
            )}

            {/* Score IA */}
            {insight.confianca !== 'hipotese' && (
              <span className="text-[10px] text-text-muted flex items-center gap-1 px-2 py-0.5 rounded-full bg-bg-hover/50">
                <Sparkles size={10} className="text-primary" />
                Score IA
              </span>
            )}
          </div>

          {/* Ações rápidas */}
          <div className="flex items-center gap-1">
            {insight.tipo === 'encalhe' && (
              <Button variant="ghost" size="sm" className="text-[10px] !px-2 !py-1">
                Criar promoção
              </Button>
            )}
            {insight.tipo === 'oportunidade_b' && (
              <Button variant="ghost" size="sm" className="text-[10px] !px-2 !py-1">
                Destacar produto
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Modal de produtos */}
      {insight.produtos && (
        <ProductListModal
          open={showProdutos}
          onClose={() => setShowProdutos(false)}
          tipo={insight.tipo}
          produtos={insight.produtos}
        />
      )}
    </div>
  )
}
