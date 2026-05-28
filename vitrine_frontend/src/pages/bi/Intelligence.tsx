/** Página principal do Vitrine Intelligence — AI Command Center. */
import { useCallback } from 'react'
import { Sparkles, BarChart3, AlertTriangle, TrendingUp, Activity, RotateCw, FileDown, RefreshCw } from 'lucide-react'
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

/** KPI rápido para o hero */
function HeroKpi({ icon, label, value, trend, color }: {
  icon: React.ReactNode
  label: string
  value: string
  trend?: string
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
      {trend && (
        <span className="text-[10px] font-medium text-success inline-flex items-center gap-0.5 mt-0.5">
          <TrendingUp size={10} />
          {trend}
        </span>
      )}
    </div>
  )
}

export default function Intelligence() {
  const { status, resultado, erro, gerarAnalise, dismissInsight } = useIntelligence()
  const { indicadores: macroIndicadores, status: macroStatus, erro: macroErro } = useMacroIndicators()

  const exportarRelatorio = useCallback(() => {
    if (!resultado) return
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
                    Análise estratégica dos últimos 30 dias — dados conectados com contexto macroeconômico
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

            {/* KPI Strip */}
            {status === 'ready' && resultado && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <HeroKpi
                  icon={<BarChart3 size={16} />}
                  label="Faturamento"
                  value="R$ 780,5k"
                  trend="12,3% vs. período anterior"
                  color="text-success"
                />
                <HeroKpi
                  icon={<AlertTriangle size={16} />}
                  label="Produtos críticos"
                  value="15"
                  trend="3 novos desde última análise"
                  color="text-danger"
                />
                <HeroKpi
                  icon={<Sparkles size={16} />}
                  label="Insights gerados"
                  value={String(resultado.insights.length)}
                  trend="Análise concluída"
                  color="text-primary"
                />
                <HeroKpi
                  icon={<Activity size={16} />}
                  label="Score operacional"
                  value="92"
                  trend="Desempenho estável"
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
              {resultado && (
                <span>
                  · Última análise: {new Date(resultado.gerado_em).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
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

        {/* ── Loading ── */}
        {status === 'loading' && (
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

        {/* ── Error ── */}
        {status === 'error' && (
          <ErrorBanner
            message={erro?.message || 'Não foi possível gerar a análise. Tente novamente.'}
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

        {/* ── Ready ── */}
        {status === 'ready' && resultado && (
          <>
            {/* Resumo Executivo */}
            <ResumoExecutivo
              texto={resultado.resumo_executivo}
              fonte={resultado.fonte}
              geradoEm={resultado.gerado_em}
            />

            {/* Quick Actions */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mr-1">
                Ações rápidas
              </span>
              <Button
                variant="secondary" size="sm"
                onClick={exportarRelatorio}
                disabled={!resultado}
              >
                <FileDown size={12} />
                Exportar relatório
              </Button>
              <Button
                variant="secondary" size="sm"
                onClick={gerarAnalise}
              >
                <RefreshCw size={12} />
                Regenerar insights
              </Button>
            </div>

            {/* Insights */}
            {resultado.insights.length === 0 ? (
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
                      {resultado.insights.length} análises
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[10px] text-text-muted">
                    <Sparkles size={10} />
                    Ordenado por severidade
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {resultado.insights.map((insight, i) => (
                    <div
                      key={insight.hash}
                      className="animate-fade-in-up"
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
