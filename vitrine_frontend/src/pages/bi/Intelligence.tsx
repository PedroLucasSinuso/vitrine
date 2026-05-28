/** Página principal do Vitrine Intelligence — análise semanal com IA. */
import { Sparkles } from 'lucide-react'
import BiPageLayout from '../../components/bi/BiPageLayout'
import Button from '../../components/ui/Button'
import Skeleton from '../../components/ui/Skeleton'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import ResumoExecutivo from '../../components/intelligence/ResumoExecutivo'
import InsightCard from '../../components/intelligence/InsightCard'
import { useIntelligence } from '../../hooks/useIntelligence'

export default function Intelligence() {
  const { status, resultado, gerarAnalise, dismissInsight } = useIntelligence()

  return (
    <BiPageLayout
      titulo="Intelligence"
      breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Intelligence' }]}
      hideSubNav
    >
      <div className="space-y-6">
        {/* ── Botão + descrição ── */}
        <div className="flex justify-between items-center gap-4 flex-wrap">
          <p className="text-sm text-text-secondary">
            Análise estratégica dos últimos 30 dias — conecta dados da loja com contexto macroeconômico.
          </p>
          <Button onClick={gerarAnalise} disabled={status === 'loading'}>
            {status === 'loading' ? 'Gerando...' : 'Gerar Análise Semanal'}
          </Button>
        </div>

        {/* ── Loading ── */}
        {status === 'loading' && (
          <div className="space-y-4">
            <Skeleton className="h-24 w-full" />
            <Skeleton variant="card" className="h-20" />
            <Skeleton variant="card" className="h-20" />
            <p className="text-center text-sm text-text-muted">
              Analisando dados da loja...
            </p>
          </div>
        )}

        {/* ── Error ── */}
        {status === 'error' && (
          <ErrorBanner message="Não foi possível gerar a análise. Tente novamente." />
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
            <ResumoExecutivo
              texto={resultado.resumo_executivo}
              fonte={resultado.fonte}
              geradoEm={resultado.gerado_em}
            />

            {resultado.insights.length === 0 && (
              <EmptyState
                icon={<Sparkles size={24} />}
                title="Nenhum insight relevante"
                description="Com base nos dados disponíveis, não foram identificados padrões que exijam atenção imediata."
              />
            )}

            {resultado.insights.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-text-primary">
                  Insights ({resultado.insights.length})
                </h3>
                {resultado.insights.map(insight => (
                  <InsightCard
                    key={insight.hash}
                    insight={insight}
                    onDismiss={() => dismissInsight(insight.hash)}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </BiPageLayout>
  )
}
