/** Card de resumo executivo premium — hero principal da página Intelligence. */
import { Sparkles, Cpu, TrendingUp, TrendingDown, Minus, ChevronRight } from 'lucide-react'
import type { Fonte } from '../../types/intelligence'
import { formatDateWithWeekday } from '../../utils/formatters'

interface Props {
  texto: string
  fonte: Fonte
  geradoEm: string
}

const FONTE_META: Record<Fonte, { label: string; icon: React.ReactNode; color: string }> = {
  claude: { label: 'Claude Sonnet', icon: <Sparkles size={12} />, color: 'text-purple-400' },
  gpt4o_mini: { label: 'GPT-4o Mini', icon: <Sparkles size={12} />, color: 'text-emerald-400' },
  deterministico: { label: 'Síntese simplificada', icon: <Cpu size={12} />, color: 'text-blue-400' },
}

/** Extrai um valor monetário do texto do resumo (ex: "R$ 780.532,89") */
function extractRevenue(text: string): string | null {
  const match = text.match(/[R]\$[\s]*[\d.,]+/)
  return match?.[0] ?? null
}

/** Extrai número de oportunidades (ex: "5 oportunidades") */
function extractOpportunities(text: string): string | null {
  const match = text.match(/(\d+)\s*oportunidades?/)
  return match?.[1] ?? null
}

/** Determina tendência baseada em palavras-chave */
function detectTrend(text: string): 'up' | 'down' | 'stable' {
  const lower = text.toLowerCase()
  if (lower.includes('crescimento') || lower.includes('aumento') || lower.includes('melhora'))
    return 'up'
  if (lower.includes('queda') || lower.includes('redução') || lower.includes('atenção'))
    return 'down'
  return 'stable'
}

const TREND_CONFIG = {
  up: { icon: TrendingUp, label: 'Tendência positiva', color: 'text-success' },
  down: { icon: TrendingDown, label: 'Atenção necessária', color: 'text-danger' },
  stable: { icon: Minus, label: 'Estável', color: 'text-text-muted' },
}

export default function ResumoExecutivo({ texto, fonte, geradoEm }: Props) {
  const meta = FONTE_META[fonte] ?? FONTE_META.deterministico
  const revenue = extractRevenue(texto)
  const opportunities = extractOpportunities(texto)
  const trend = detectTrend(texto)
  const TrendIcon = TREND_CONFIG[trend].icon

  return (
    <div className="hero-card p-6 sm:p-8 relative overflow-hidden group">
      {/* Orbe decorativo sutil */}
      <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-primary/5 blur-3xl pointer-events-none group-hover:bg-primary/[0.07] transition-colors duration-700" />

      {/* Grid principal */}
      <div className="relative grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Coluna 1 — Texto + metadata */}
        <div className="lg:col-span-2 space-y-4">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-primary/[0.12] text-primary shadow-sm shrink-0">
                <Sparkles size={22} />
              </div>
              <div className="min-w-0">
                <h2 className="text-lg font-bold text-text-primary font-display tracking-tight">
                  Resumo Executivo
                </h2>
                <p className="text-[11px] text-text-muted">
                  Análise estratégica · {formatDateWithWeekday(geradoEm.split('T')[0])}
                </p>
              </div>
            </div>

            {/* Fonte badge */}
            <div className={`self-start sm:self-auto inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border border-border/40 ${meta.color} bg-bg-hover/50 shrink-0`}>
              {meta.icon}
              {meta.label}
            </div>
          </div>

          {/* Texto principal com tipografia melhorada */}
          <p className="text-sm text-text-secondary leading-relaxed">
            {texto}
          </p>

          {/* Quick action */}
          <button className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:text-primary-hover transition-colors group/btn">
            Ver análise completa
            <ChevronRight size={14} className="group-hover/btn:translate-x-0.5 transition-transform" />
          </button>
        </div>

        {/* Coluna 2 — KPIs visuais */}
        <div className="space-y-4">
          {/* Score de confiança */}
          <div className="bg-bg-hover/40 rounded-xl p-4 border border-border/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold text-text-muted uppercase tracking-wider">
                Confiança IA
              </span>
              <span className="text-xs font-bold text-success">
                {fonte === 'deterministico' ? '100%' : '92%'}
              </span>
            </div>
            {/* Barra de progresso */}
            <div className="h-1.5 bg-bg-hover rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary to-info rounded-full transition-all duration-700"
                style={{ width: fonte === 'deterministico' ? '100%' : '92%' }}
              />
            </div>
          </div>

          {/* Cards KPI rápidos */}
          <div className="grid grid-cols-2 gap-2 sm:gap-3">
            {revenue && (
              <div className="bg-bg-hover/30 rounded-xl p-3 border border-border/20">
                <span className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                  Faturamento
                </span>
                <p className="text-lg font-bold text-text-primary font-display mt-0.5">
                  {revenue}
                </p>
              </div>
            )}
            {opportunities && (
              <div className="bg-bg-hover/30 rounded-xl p-3 border border-border/20">
                <span className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                  Oportunidades
                </span>
                <p className="text-lg font-bold text-text-primary font-display mt-0.5">
                  {opportunities}
                </p>
              </div>
            )}
            <div className="bg-bg-hover/30 rounded-xl p-3 border border-border/20">
              <span className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                Tendência
              </span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <TrendIcon size={16} className={TREND_CONFIG[trend].color} />
                <span className={`text-xs font-semibold ${TREND_CONFIG[trend].color}`}>
                  {TREND_CONFIG[trend].label}
                </span>
              </div>
            </div>
            <div className="bg-bg-hover/30 rounded-xl p-3 border border-border/20">
              <span className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">
                Score
              </span>
              <p className="text-lg font-bold text-text-primary font-display mt-0.5">
                {fonte === 'deterministico' ? '—' : 'A'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
