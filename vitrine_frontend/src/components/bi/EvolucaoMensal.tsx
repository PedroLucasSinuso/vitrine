import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { CHART_THEME } from '../../config/chartTheme'
import type { PontoMensal } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { formatarDecimal, rotuloMes } from '../../utils/equipe'

interface Props {
  pontos: PontoMensal[]
  descricao: string
  mostrarAtivos?: boolean
}

function celula(valor: number | null, formatar: (v: number) => string): string {
  return valor === null ? '—' : formatar(valor)
}

function situacao(p: PontoMensal): string | null {
  if (p.sem_dados) return 'sem relatório'
  if (p.ausente) return 'não vendeu'
  return p.parcial ? 'parcial' : null
}

export default function EvolucaoMensal({ pontos, descricao, mostrarAtivos = false }: Props) {
  const dados = pontos.map((p) => ({ rotulo: rotuloMes(p.competencia), valor: p.faturamento_liquido }))
  return (
    <div className="flex flex-col gap-3">
      <div role="img" aria-label={descricao}>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={dados} margin={CHART_THEME.margin}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
            <XAxis dataKey="rotulo" tick={CHART_THEME.yAxis.tick} axisLine={{ stroke: 'var(--color-border)' }} tickLine={false} />
            <YAxis tickFormatter={(v: number) => `${(v / 1000).toLocaleString('pt-BR')}k`} tick={CHART_THEME.yAxis.tick} axisLine={false} tickLine={false} width={44} />
            <Tooltip
              contentStyle={CHART_THEME.tooltip.contentStyle}
              formatter={((v: number) => [formatCurrency(v), 'Faturamento líquido']) as never}
            />
            <Line type="monotone" dataKey="valor" stroke="var(--color-primary)" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} connectNulls={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <caption className="sr-only">{descricao}</caption>
          <thead>
            <tr className="text-left text-text-muted">
              <th scope="col" className="py-1 pr-3 font-medium">Mês</th>
              <th scope="col" className="py-1 pr-3 font-medium text-right">Faturamento líquido</th>
              <th scope="col" className="py-1 pr-3 font-medium text-right">Ticket médio</th>
              <th scope="col" className="py-1 pr-3 font-medium text-right">PA</th>
              {mostrarAtivos && <th scope="col" className="py-1 font-medium text-right">Vendedores</th>}
            </tr>
          </thead>
          <tbody>
            {pontos.map((p) => (
              <tr key={p.competencia} className="border-t border-border text-text-secondary">
                <th scope="row" className="py-1 pr-3 text-left font-medium text-text-primary whitespace-nowrap">
                  {rotuloMes(p.competencia)}
                  {situacao(p) && <span className="ml-2 font-normal text-text-muted">({situacao(p)})</span>}
                </th>
                <td className="py-1 pr-3 text-right">{celula(p.faturamento_liquido, formatCurrency)}</td>
                <td className="py-1 pr-3 text-right">{celula(p.ticket_medio, formatCurrency)}</td>
                <td className="py-1 pr-3 text-right">{celula(p.pa, formatarDecimal)}</td>
                {mostrarAtivos && <td className="py-1 text-right">{p.vendedores_ativos ?? '—'}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
