import { CalendarDays, Clock } from 'lucide-react'
import Card from '../ui/Card'
import type { PontoDiarioDTO, DiarioComparativoDTO } from '../../types'
import { formatCurrency, formatDateWithWeekday } from '../../utils/formatters'

/* ── Badge de Variação (▲/▼) ── */
function BadgeVariacao({ atual, comp }: { atual: number; comp: DiarioComparativoDTO | null }) {
  const antVal = comp?.valor_offset ?? null
  const rotuloBase = comp?.rotulo ?? 'vs período anterior'

  let diff: number | null = null
  if (antVal !== null) {
    if (antVal === 0 && atual > 0) {
      diff = 100
    } else if (antVal > 0) {
      diff = ((atual / antVal) - 1) * 100
    }
  }

  if (diff === null) return <span className="block h-[18px]" />

  const isPositive = diff >= 0
  return (
    <span className={`text-xs font-semibold inline-flex items-center gap-1.5 ${isPositive ? 'text-success' : 'text-danger'}`}>
      <span className="text-sm leading-none">{isPositive ? '▲' : '▼'}</span>
      {Math.abs(diff).toFixed(1)}%
      <span className="text-text-muted font-normal text-[10px]">{rotuloBase}</span>
    </span>
  )
}

/* ── Linha "Ano passado: R$ X" ── */
function LinhaOffset({ comp, fmt }: { comp: DiarioComparativoDTO | null; fmt: (v: number) => string }) {
  if (comp?.valor_offset == null) return <p className="h-[14px]" />
  return (
    <p className="text-[11px] text-text-muted leading-tight h-[14px]">
      Ano passado: <span className="font-medium text-text-secondary">{fmt(comp.valor_offset)}</span>
    </p>
  )
}

/* ── Resumo do Dia ── */
interface ResumoDiaProps {
  receita: PontoDiarioDTO[]
  tickets: PontoDiarioDTO[]
  ticketMedio: PontoDiarioDTO[]
  comparar: boolean
  comparativo?: {
    receita: DiarioComparativoDTO | null
    tickets: DiarioComparativoDTO | null
    ticketMedio: DiarioComparativoDTO | null
  } | null
}

export default function ResumoDia({ receita, tickets, ticketMedio, comparar: compAtivo, comparativo }: ResumoDiaProps) {
  const sorted = [...receita].sort((a, b) => b.data.localeCompare(a.data))
  const ultimo = sorted[0]
  if (!ultimo) return null

  const valorReceita = receita.find((t) => t.data === ultimo.data)?.valor ?? 0
  const valorTickets = tickets.find((t) => t.data === ultimo.data)?.valor ?? 0
  const valorTicketMedio = ticketMedio.find((t) => t.data === ultimo.data)?.valor ?? 0

  const compReceita = compAtivo ? comparativo?.receita ?? null : null
  const compTickets = compAtivo ? comparativo?.tickets ?? null : null
  const compTicketMedio = compAtivo ? comparativo?.ticketMedio ?? null : null

  const ultimoEParcial = !!compReceita?.parcial_ate
  const parcialAte = compReceita?.parcial_ate ?? null

  return (
    <Card variant="elevated" padding="md">
      <div className="flex items-center gap-3 pb-4 border-b border-border mb-4">
        <div className="p-2 rounded-xl bg-primary-light text-primary shrink-0">
          <CalendarDays size={16} />
        </div>
        <div className="flex-1 min-w-0">
          <span className="text-xs font-semibold text-text-primary">{formatDateWithWeekday(ultimo.data)}</span>
        </div>
        {ultimoEParcial && parcialAte && (
          <span className="text-[10px] text-warning bg-warning-light px-2 py-0.5 rounded-full font-medium inline-flex items-center gap-1 shrink-0">
            <Clock size={10} /> Parcial até {parcialAte}
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-8">
        {/* Vendas */}
        <div className="flex flex-col gap-1.5">
          <p className="text-[10px] font-mono font-bold uppercase tracking-[0.12em] text-text-muted">Vendas</p>
          <p className="text-xl font-bold text-text-primary tabular-nums tracking-tight">{formatCurrency(valorReceita)}</p>
          <BadgeVariacao atual={valorReceita} comp={compReceita} />
          <LinhaOffset comp={compReceita} fmt={formatCurrency} />
        </div>

        {/* Tickets */}
        <div className="flex flex-col gap-1.5">
          <p className="text-[10px] font-mono font-bold uppercase tracking-[0.12em] text-text-muted">Tickets</p>
          <p className="text-xl font-bold text-text-primary tabular-nums tracking-tight">{Math.round(valorTickets).toLocaleString('pt-BR')}</p>
          <BadgeVariacao atual={valorTickets} comp={compTickets} />
          <LinhaOffset comp={compTickets} fmt={(v) => Math.round(v).toLocaleString('pt-BR')} />
        </div>

        {/* Ticket Médio */}
        <div className="flex flex-col gap-1.5">
          <p className="text-[10px] font-mono font-bold uppercase tracking-[0.12em] text-text-muted">Ticket Médio</p>
          <p className="text-xl font-bold text-text-primary tabular-nums tracking-tight">{formatCurrency(valorTicketMedio)}</p>
          <BadgeVariacao atual={valorTicketMedio} comp={compTicketMedio} />
          <LinhaOffset comp={compTicketMedio} fmt={formatCurrency} />
        </div>
      </div>
    </Card>
  )
}
