import { format, formatDistanceToNow } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import { RefreshCw, Clock } from 'lucide-react'
import PeriodoForm, { type Preset } from './PeriodoForm'
import ExportButtons from './ExportButtons'
import Card from '../ui/Card'
import type { PeriodoBi } from '../../types'

const PRESETS_DASHBOARD: Preset[] = [
  { label: 'Hoje', kind: 'days', days: 0 },
  { label: '7 dias', kind: 'days', days: 7 },
  { label: '30 dias', kind: 'days', days: 30 },
  { label: 'Este mês', kind: 'current_month' },
  { label: 'Mês passado', kind: 'last_month' },
]

interface DashboardTopBarProps {
  periodo: PeriodoBi
  setPeriodo: (p: PeriodoBi) => void
  loading: boolean
  comparar: boolean
  onToggleComparar: () => void
  onBuscar: (p?: PeriodoBi) => void
  disabled: boolean
  cacheTimestamp: number | null
  cacheFresh: boolean
  dadosParciaisAte: string | null
  onExcel: () => void
  onPdf: () => void
  onCsv: () => void
}

export default function DashboardTopBar({
  periodo, setPeriodo, loading, comparar, onToggleComparar,
  onBuscar, disabled, cacheTimestamp, cacheFresh,
  dadosParciaisAte, onExcel, onPdf, onCsv,
}: DashboardTopBarProps) {
  return (
    <Card variant="bordered" padding="md">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        {/* Left: periodo form */}
        <div className="flex-1 min-w-0">
          <PeriodoForm
            value={periodo}
            onChange={setPeriodo}
            onBuscar={onBuscar}
            loading={loading}
            presets={PRESETS_DASHBOARD}
          />
        </div>

        {/* Right: controls inline */}
        <div className="flex items-center gap-3 shrink-0 flex-wrap">
          {/* Comparar toggle */}
          <button
            onClick={onToggleComparar}
            className={`
              text-xs font-semibold px-3 py-1.5 rounded-full transition-all whitespace-nowrap
              ${comparar
                ? 'bg-primary text-white shadow-sm'
                : 'bg-bg-hover text-text-secondary hover:bg-primary-lighter hover:text-primary'
              }
            `}
          >
            {comparar ? 'Comparando com ano anterior' : 'Comparar com ano anterior'}
          </button>

          {/* Export */}
          <ExportButtons
            onExcel={onExcel}
            onPdf={onPdf}
            onCsv={onCsv}
            disabled={disabled}
          />
        </div>
      </div>

      {/* Status bar — subtle, below the main row */}
      <div className="flex items-center gap-3 mt-3 pt-3 border-t border-border">
        {cacheTimestamp && (
          <span
            className="flex items-center gap-1.5 text-[11px] text-text-muted font-medium"
            title={`Cache atualizado às ${format(new Date(cacheTimestamp), 'HH:mm:ss')}`}
          >
            <RefreshCw size={10} className={cacheFresh ? 'text-success' : 'text-warning'} />
            {formatDistanceToNow(new Date(cacheTimestamp), { locale: ptBR, addSuffix: true })}
          </span>
        )}
        {dadosParciaisAte && (
          <span className="text-[11px] text-warning bg-warning-light px-2 py-0.5 rounded-full font-medium inline-flex items-center gap-1">
            <Clock size={10} /> Parcial até {dadosParciaisAte}
          </span>
        )}
      </div>
    </Card>
  )
}
