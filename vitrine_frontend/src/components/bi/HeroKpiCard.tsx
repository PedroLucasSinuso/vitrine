import KpiCard from '../ui/KpiCard'

interface MetaInfo {
  pct: number
  atual: number
  meta: number
}

interface ProjecaoInfo {
  valor: number
  vsMetaPct: number | null
  diasCorridos: number
  diasTotal: number
  mediaDiaria: number
}

interface Props {
  label: string
  valor: string
  pulseKey?: number
  variacao?: { valor: number; direcao: 'positivo' | 'negativo' | 'estavel' } | null
  valorAnterior?: string
  meta?: MetaInfo | null
  projecao?: ProjecaoInfo | null
}

export default function HeroKpiCard({ meta, projecao, ...rest }: Props) {
  return <KpiCard {...rest} meta={meta} projecao={projecao} hero />
}
