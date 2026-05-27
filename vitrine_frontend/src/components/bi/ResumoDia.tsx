import { useEffect, useState } from 'react'
import { CalendarDays, Clock } from 'lucide-react'
import { format } from 'date-fns'
import Card from '../ui/Card'
import Skeleton from '../ui/Skeleton'
import { getConfigsCache } from '../../stores/configStore'
import { fetchDiario, fetchDiarioComparativo } from '../../api/bi'
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

/* ── Resumo do Dia (sempre HOJE, independente do período selecionado) ── */
export default function ResumoDia() {
  const [marketName, setMarketName] = useState<string | null>(null)
  const [receita, setReceita] = useState<PontoDiarioDTO[]>([])
  const [tickets, setTickets] = useState<PontoDiarioDTO[]>([])
  const [ticketMedio, setTicketMedio] = useState<PontoDiarioDTO[]>([])
  const [comparativo, setComparativo] = useState<{
    receita: DiarioComparativoDTO | null
    tickets: DiarioComparativoDTO | null
    ticketMedio: DiarioComparativoDTO | null
  }>({ receita: null, tickets: null, ticketMedio: null })
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    getConfigsCache().then((c) => {
      if (c.marketName) setMarketName(c.marketName)
    }).catch(() => {})
  }, [])

  // Busca dados APENAS do dia atual, independente do período do Dashboard
  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal
    const hoje = format(new Date(), 'yyyy-MM-dd')
    const periodoHoje = { data_inicio: hoje, data_fim: hoje }

    Promise.all([
      fetchDiario(periodoHoje, 'receita_produto', signal),
      fetchDiario(periodoHoje, 'qtd_tickets', signal),
      fetchDiario(periodoHoje, 'ticket_medio', signal),
      fetchDiarioComparativo(periodoHoje, 'receita_produto', signal),
      fetchDiarioComparativo(periodoHoje, 'qtd_tickets', signal),
      fetchDiarioComparativo(periodoHoje, 'ticket_medio', signal),
    ])
      .then(([rc, tk, tm, compRc, compTk, compTm]) => {
        setReceita(rc)
        setTickets(tk)
        setTicketMedio(tm)
        setComparativo({ receita: compRc, tickets: compTk, ticketMedio: compTm })
      })
      .catch((e: unknown) => {
        const err = e as { name?: string }
        if (err?.name === 'CanceledError' || err?.name === 'AbortError') return
        setErro('Indisponível')
      })
      .finally(() => setLoading(false))

    return () => controller.abort()
  }, [])

  const hojeStr = format(new Date(), 'yyyy-MM-dd')
  const valorReceita = receita.find((r) => r.data === hojeStr)?.valor ?? 0
  const valorTickets = tickets.find((t) => t.data === hojeStr)?.valor ?? 0
  const valorTicketMedio = ticketMedio.find((t) => t.data === hojeStr)?.valor ?? 0

  const compReceita = comparativo.receita
  const compTickets = comparativo.tickets
  const compTicketMedio = comparativo.ticketMedio

  const ultimoEParcial = !!compReceita?.parcial_ate
  const parcialAte = compReceita?.parcial_ate ?? null

  return (
    <Card variant="elevated" padding="md">
      <div className="flex flex-col items-center gap-1 pb-4 border-b border-border mb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-primary-light text-primary">
            <CalendarDays size={14} />
          </div>
          <span className="text-sm font-semibold text-text-primary text-center">
            {marketName ? `${marketName} — ` : ''}Hoje
          </span>
        </div>
        <span className="text-[11px] text-text-muted">{formatDateWithWeekday(hojeStr)}</span>
        {ultimoEParcial && parcialAte && (
          <span className="text-[10px] text-warning bg-warning-light px-2 py-0.5 rounded-full font-medium inline-flex items-center gap-1">
            <Clock size={10} /> Parcial até {parcialAte}
          </span>
        )}
      </div>

      {loading && (
        <div className="grid grid-cols-3 gap-8">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-2">
              <Skeleton className="h-3 w-12" />
              <Skeleton className="h-7 w-24" />
              <Skeleton className="h-3 w-16" />
            </div>
          ))}
        </div>
      )}

      {!loading && erro && (
        <p className="text-center text-sm text-text-muted py-4">{erro}</p>
      )}

      {!loading && !erro && (
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
      )}
    </Card>
  )
}
