import KpiCard from '../ui/KpiCard'

interface Props {
  label: string
  valor: string
  pulseKey?: number
  variacao?: { valor: number; direcao: 'positivo' | 'negativo' | 'estavel' } | null
  valorAnterior?: string
}

export default function HeroKpiCard(props: Props) {
  return <KpiCard label={props.label} value={props.valor} pulseKey={props.pulseKey} variacao={props.variacao} valorAnterior={props.valorAnterior} hero />
}
