import { subDays, startOfMonth, endOfMonth, subMonths, format } from 'date-fns'

export interface Preset {
  label: string
  kind: 'days' | 'current_month' | 'last_month'
  days?: number
}

function computePreset(preset: Preset): { data_inicio: string; data_fim: string } {
  const hoje = new Date()
  if (preset.kind === 'days') {
    return {
      data_inicio: format(subDays(hoje, preset.days!), 'yyyy-MM-dd'),
      data_fim: format(hoje, 'yyyy-MM-dd'),
    }
  }
  if (preset.kind === 'current_month') {
    return {
      data_inicio: format(startOfMonth(hoje), 'yyyy-MM-dd'),
      data_fim: format(hoje, 'yyyy-MM-dd'),
    }
  }
  if (preset.kind === 'last_month') {
    const mesPassado = subMonths(hoje, 1)
    return {
      data_inicio: format(startOfMonth(mesPassado), 'yyyy-MM-dd'),
      data_fim: format(endOfMonth(mesPassado), 'yyyy-MM-dd'),
    }
  }
  return { data_inicio: format(hoje, 'yyyy-MM-dd'), data_fim: format(hoje, 'yyyy-MM-dd') }
}

interface Props {
  value: { data_inicio: string; data_fim: string }
  onChange: (v: { data_inicio: string; data_fim: string }) => void
  onBuscar?: () => void
  loading?: boolean
  presets?: Preset[]
}

export default function PeriodoForm({ value, onChange, onBuscar, loading, presets }: Props) {
  return (
    <div className="flex flex-col gap-3">
      {presets && (
        <div className="flex gap-1.5 flex-wrap">
          {presets.map((p) => (
            <button
              key={p.label}
              type="button"
              onClick={() => onChange(computePreset(p))}
              className="text-xs px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-primary-lighter hover:text-primary dark:hover:text-primary transition"
            >
              {p.label}
            </button>
          ))}
        </div>
      )}
      <div className="flex flex-wrap gap-2 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500 dark:text-gray-400">De</label>
          <input
            type="date"
            className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            value={value.data_inicio}
            onChange={(e) => onChange({ ...value, data_inicio: e.target.value })}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-gray-500 dark:text-gray-400">Até</label>
          <input
            type="date"
            className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            value={value.data_fim}
            onChange={(e) => onChange({ ...value, data_fim: e.target.value })}
          />
        </div>
        {onBuscar && (
          <button
            onClick={onBuscar}
            disabled={loading}
            className="bg-primary hover:bg-primary-hover text-white font-semibold px-5 py-2 rounded-lg transition disabled:opacity-50 text-sm"
          >
            {loading ? 'Buscando...' : 'Buscar'}
          </button>
        )}
      </div>
    </div>
  )
}
