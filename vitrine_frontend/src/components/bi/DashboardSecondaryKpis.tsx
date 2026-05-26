import KpiCard from './KpiCard'
import Skeleton from '../ui/Skeleton'
import type { VariacaoInfo } from '../../pages/bi/dashboardHelpers'

interface KpiData {
  label: string
  valor: string
  delay: number
  variacao: VariacaoInfo | null
  valorAnterior: string | undefined
}

interface DashboardSecondaryKpisProps {
  items: KpiData[]
  loading: boolean
  visible: boolean
}

export default function DashboardSecondaryKpis({ items, loading, visible }: DashboardSecondaryKpisProps) {
  if (visible) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {items.map((kpi) => (
          <KpiCard
            key={kpi.label}
            label={kpi.label}
            valor={kpi.valor}
            delay={kpi.delay}
            variacao={kpi.variacao}
            valorAnterior={kpi.valorAnterior}
          />
        ))}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="grid grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} variant="kpi" />
        ))}
      </div>
    )
  }

  return null
}
