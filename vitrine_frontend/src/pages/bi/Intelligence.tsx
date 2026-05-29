/** Página principal do Vitrine Intelligence — AI Command Center. */
import { useCallback, useRef } from 'react'
import { Sparkles, BarChart3, AlertTriangle, Activity, RotateCw, FileDown, RefreshCw } from 'lucide-react'
import BiPageLayout from '../../components/bi/BiPageLayout'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import ResumoExecutivo from '../../components/intelligence/ResumoExecutivo'
import InsightCard from '../../components/intelligence/InsightCard'
import MacroStrip from '../../components/intelligence/MacroStrip'
import { useIntelligence } from '../../hooks/useIntelligence'
import { useMacroIndicators } from '../../hooks/useMacroIndicators'
import type { IntelligenceResponse } from '../../types/intelligence'
import { formatCurrency, formatDataBrasil } from '../../utils/formatters'

/** KPI rápido para o hero — sem dados fake, sem trend enganosa. */
function HeroKpi({ icon, label, value, color }: {
  icon: React.ReactNode
  label: string
  value: string
  color?: string
}) {
  return (
    <div className="bg-bg-hover/30 rounded-xl p-3 sm:p-4 border border-border/20 hover:border-border/40 transition-colors">
      <div className="flex items-center gap-2 mb-1.5">
        <span className={color || 'text-primary'}>{icon}</span>
        <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
          {label}
        </span>
      </div>
      <p className="text-lg sm:text-xl font-bold text-text-primary font-display tracking-tight">
        {value}
      </p>
    </div>
  )
}

export default function Intelligence() {
  const { status, resultado, erro, gerarAnalise, dismissInsight } = useIntelligence()
  const { indicadores: macroIndicadores, status: macroStatus, erro: macroErro } = useMacroIndicators()
  /** Preserva o último resultado bem-sucedido para manter UI visível durante regeneração. */
  const ultimoResultadoRef = useRef<IntelligenceResponse | null>(null)
  /** Usa resultado atual ou o preservado (fallback durante loading/error de regeneração). */
  const exibicao = resultado ?? ultimoResultadoRef.current

  // Atualiza o ref sempre que um resultado novo chega
  if (resultado && resultado !== ultimoResultadoRef.current) {
    ultimoResultadoRef.current = resultado
  }

  const exportarRelatorio = useCallback(() => {
    if (!exibicao) return
    const blob = new Blob([JSON.stringify(resultado, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `intelligence_${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [resultado])

  return (
    <BiPageLayout
      titulo="Intelligence"
      breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Intelligence' }]}
      hideSubNav
    >
      <div className="space-y-6">
        {/* ════════════════════════════════════════════
           HERO — AI Command Center
           ════════════════════════════════════════════ */}
        <div className="relative overflow-hidden rounded-2xl border border-border/40 bg-gradient-to-br from-primary/[0.05] via-bg-card to-primary/[0.02] p-6 sm:p-8">
          {/* Orbes decorativos */}
          <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary/5 blur-3xl pointer-events-none" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-info/5 blur-3xl pointer-events-none" />

          <div className="relative space-y-6">
            {/* Header row */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-primary/[0.12] text-primary shadow-sm">
                  <Sparkles size={24} />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-text-primary font-display tracking-tight">
                    Command Center
                  </h1>
                  <p className="text-xs text-text-muted mt-0.5">
                    Análise estratégica dos últimos 30 dias — apenas produtos ativos (com venda em 90d) com contexto macroeconômico
                  </p>
                </div>
              </div>

              {/* Botão integrado ao hero */}
              <Button
                onClick={gerarAnalise}
                disabled={status === 'loading'}
                size="lg"
                className="shrink-0 shadow-lg shadow-primary/20"
              >
                {status === 'loading' ? (
                  <>
                    <RotateCw size={16} className="animate-spin" />
                    Gerando...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    Gerar Análise Semanal
                  </>
                )}
              </Button>
            </div>

            {/* KPI Strip — dados reais do backend */}
            {status === 'ready' && resultado?.kpis && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <HeroKpi
                  icon={<BarChart3 size={16} />}
                  label="Faturamento"
                  value={resultado.kpis.faturamento != null ? formatCurrency(resultado.kpis.faturamento) : '\u2014'}
                  color="text-success"
                />
                <HeroKpi
                  icon={<AlertTriangle size={16} />}
                  label="Alertas críticos"
                  value={String(resultado.kpis.alertas_alto_impacto)}
                  color={resultado.kpis.alertas_alto_impacto > 0 ? 'text-danger' : 'text-text-muted'}
                />
                <HeroKpi
                  icon={<Sparkles size={16} />}
                  label="Insights gerados"
                  value={String(resultado.kpis.total_insights)}
                  color="text-primary"
                />
                <HeroKpi
                  icon={<Activity size={16} />}
                  label="Frentes analisadas"
                  value={String(resultado.kpis.tipos_insight.length)}
                  color="text-info"
                />
              </div>
            )}

            {/* Status indicator */}
            <div className="flex items-center gap-3 text-[11px] text-text-muted">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-success animate-status-pulse" />
                {status === 'ready' ? 'Análise disponível' : status === 'loading' ? 'Processando...' : 'Sistema online'}
              </span>
              {exibicao && (
                <span>
                  · Última análise: {formatDataBrasil(exibicao.gerado_em)}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* ── Macro Indicators Strip ── */}
        <MacroStrip
          indicadores={macroIndicadores}
          loading={macroStatus === 'loading'}
          erro={macroErro}
        />

        {/* ── Loading (primeira vez — sem resultado anterior) ── */}
        {status === 'loading' && !exibicao && (
          <div className="space-y-4">
            <Skeleton className="h-32 w-full rounded-xl" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Skeleton variant="card" className="h-28" />
              <Skeleton variant="card" className="h-28" />
            </div>
            <p className="text-center text-sm text-text-muted animate-status-pulse">
              Analisando dados da loja...
            </p>
          </div>
        )}

        {/* ── Error (sem resultado anterior — primeira tentativa) ── */}
        {status === 'error' && !exibicao && (
          <ErrorBanner
            message={erro?.message || 'Não foi possível gerar a análise. Tente novamente.'}
          />
        )}

        {/* ── Error (regeneração falhou — manter resultado anterior visível) ── */}
        {status === 'error' && exibicao && (
          <ErrorBanner
            message={erro?.message || 'Erro ao regenerar insights. Exibindo última análise disponível.'}
          />
        )}

        {/* ── Idle (primeira vez) ── */}
        {status === 'idle' && (
          <EmptyState
            icon={<Sparkles size={32} />}
            title="Nenhuma análise gerada ainda"
            description="Clique em 'Gerar Análise Semanal' para receber recomendações estratégicas baseadas nos dados da sua loja."
          />
        )}

        {/* ── Ready / regenerando / erro regeneração (mantém conteúdo visível) ── */}
        {(status === 'ready' || (status === 'loading' && exibicao) || (status === 'error' && exibicao)) && exibicao && (
          <>
            {/* Resumo Executivo */}
            <ResumoExecutivo
              texto={exibicao.resumo_executivo}
              fonte={exibicao.fonte}
              geradoEm={exibicao.gerado_em}
            />

            {/* Quick Actions */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-2">
              <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider sm:mr-1">
                Ações rápidas
              </span>
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <Button
                  variant="secondary" size="sm"
                  onClick={exportarRelatorio}
                  disabled={status === 'loading'}
                  className="flex-1 sm:flex-initial"
                >
                  <FileDown size={12} />
                  Exportar relatório
                </Button>
                <Button
                  variant="secondary" size="sm"
                  onClick={gerarAnalise}
                  disabled={status === 'loading'}
                  className="flex-1 sm:flex-initial"
                >
                  {status === 'loading' ? (
                    <RotateCw size={12} className="animate-spin" />
                  ) : (
                    <RefreshCw size={12} />
                  )}
                  {status === 'loading' ? 'Regenerando...' : 'Regenerar insights'}
                </Button>
              </div>
            </div>

            {/* Overlay de regeneração (só quando está carregando) */}
            {status === 'loading' && (
              <div className="relative">
                <div className="absolute inset-0 bg-bg-card/40 backdrop-blur-[1px] z-10 flex items-center justify-center rounded-xl min-h-[120px]">
                  <div className="flex items-center gap-2 text-sm text-text-muted">
                    <RotateCw size={16} className="animate-spin" />
                    Atualizando insights...
                  </div>
                </div>
              </div>
            )}

            {/* Insights */}
            {exibicao.insights.length === 0 ? (
              <EmptyState
                icon={<Sparkles size={24} />}
                title="Nenhum insight relevante"
                description="Com base nos dados disponíveis, não foram identificados padrões que exijam atenção imediata."
              />
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <h3 className="text-sm font-bold text-text-primary font-display tracking-tight">
                      Insights Estratégicos
                    </h3>
                    <span className="text-[10px] font-medium text-text-muted bg-bg-hover/50 px-2 py-0.5 rounded-full">
                      {exibicao.insights.length} análises
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[10px] text-text-muted">
                    <Sparkles size={10} />
                    Ordenado por severidade
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {exibicao.insights.map((insight, i) => (
                    <div
                      key={insight.hash}
                      className="motion-safe:animate-fade-in-up"
                      style={{ animationDelay: `${i * 60}ms` }}
                    >
                      <InsightCard
                        insight={insight}
                        onDismiss={() => dismissInsight(insight.hash)}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </BiPageLayout>
  )
}
