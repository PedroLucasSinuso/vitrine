import { BarChart3, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import HeroKpiCard from './HeroKpiCard'
import Card from '../ui/Card'
import SectionHeader from '../ui/SectionHeader'
import Skeleton from '../ui/Skeleton'
import { formatCurrency } from '../../utils/formatters'
import type { ItemRankingDTO } from '../../types'
import type { VariacaoInfo } from '../../pages/bi/dashboardHelpers'

interface DashboardHeroProps {
  fatBruto: string
  pulseKey: number
  fatBrutoVariacao: VariacaoInfo | null
  fatBrutoAnterior: string | undefined
  pctMeta: number | null
  loadingMeta: boolean
  receitaMesAtual: number
  metaMensal: number
  projecao: number | null
  projecaoVsMeta: number | null
  diasCorridos: number
  ultimoDiaMes: number
  topProdutos: ItemRankingDTO[]
  loading: boolean
  kpisAtivos: boolean
}

export default function DashboardHero({
  fatBruto, pulseKey, fatBrutoVariacao, fatBrutoAnterior,
  pctMeta, loadingMeta, receitaMesAtual, metaMensal,
  projecao, projecaoVsMeta, diasCorridos, ultimoDiaMes,
  topProdutos, loading, kpisAtivos,
}: DashboardHeroProps) {
  const navigate = useNavigate()

  return (
    <>
      {kpisAtivos && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* ── Hero KPI (2/3) ── */}
          <div className="lg:col-span-2">
            <HeroKpiCard
              label="Faturamento Bruto"
              valor={fatBruto}
              pulseKey={pulseKey}
              variacao={fatBrutoVariacao}
              valorAnterior={fatBrutoAnterior}
              meta={!loadingMeta && pctMeta != null ? {
                pct: pctMeta,
                atual: receitaMesAtual ?? 0,
                meta: metaMensal ?? 0,
              } : null}
              projecao={!loadingMeta && projecao != null ? {
                valor: projecao,
                vsMetaPct: projecaoVsMeta,
                diasCorridos,
                diasTotal: ultimoDiaMes,
                mediaDiaria: receitaMesAtual != null && diasCorridos > 0 ? receitaMesAtual / diasCorridos : 0,
              } : null}
            />
          </div>

          {/* ── Top Produtos (1/3) ── */}
          <div className="flex flex-col">
            {topProdutos.length > 0 ? (
              <Card variant="bordered" padding="sm" className="flex-1">
                <SectionHeader
                  icon={BarChart3}
                  action={
                    <button
                      onClick={() => navigate('/bi/ranking')}
                      className="text-xs text-primary hover:text-primary-hover font-medium flex items-center gap-1 transition whitespace-nowrap"
                    >
                      Ver completo <ArrowRight size={12} />
                    </button>
                  }
                >
                  Top Produtos
                </SectionHeader>
                <div className="flex flex-col gap-0.5 mt-2">
                  {topProdutos.map((item, i) => (
                    <div
                      key={item.codigo}
                      onClick={() => navigate(`/bi/sku?codigo=${item.codigo}`)}
                      className="group flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-bg-hover cursor-pointer transition"
                    >
                      <span className={`
                        text-xs font-bold w-5 h-5 shrink-0 flex items-center justify-center rounded-full
                        ${i === 0 ? 'bg-primary/15 text-primary' : i === 1 ? 'bg-chart-2/15 text-chart-2' : i === 2 ? 'bg-chart-3/15 text-chart-3' : 'bg-bg-hover text-text-muted'}
                      `}>
                        {i + 1}
                      </span>
                      <span className="flex-1 text-sm text-text-primary truncate min-w-0" title={item.produto}>
                        {item.produto}
                      </span>
                      <span className="text-xs font-semibold text-text-primary shrink-0 tabular-nums">
                        {formatCurrency(item.valor)}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            ) : loading ? (
              <Card variant="bordered" padding="sm" className="flex-1">
                <Skeleton className="h-5 w-36 mb-3" />
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3 px-2 py-1.5">
                    <Skeleton className="h-4 w-5 rounded-full" />
                    <Skeleton className="h-4 flex-1" />
                    <Skeleton className="h-4 w-16" />
                  </div>
                ))}
              </Card>
            ) : (
              <Card variant="bordered" padding="sm" className="flex-1">
                <SectionHeader icon={BarChart3}>Top Produtos</SectionHeader>
                <p className="text-xs text-text-muted mt-2">Carregue um período para ver o ranking.</p>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* ── Loading skeleton for hero + ranking ── */}
      {loading && !kpisAtivos && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2">
            <Skeleton variant="kpi" className="h-48" />
          </div>
          <Skeleton variant="kpi" className="h-48" />
        </div>
      )}
    </>
  )
}
