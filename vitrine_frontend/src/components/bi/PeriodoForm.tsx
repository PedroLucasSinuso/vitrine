import { subDays, startOfMonth, endOfMonth, subMonths, format, differenceInDays } from 'date-fns'

const MAX_BI_DAYS = 180

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
  onBuscar?: (periodoOverride?: { data_inicio: string; data_fim: string }) => void
  loading?: boolean
  presets?: Preset[]
}

function presetAtivo(p: Preset, value: { data_inicio: string; data_fim: string }): boolean {
  const computed = computePreset(p)
  return computed.data_inicio === value.data_inicio && computed.data_fim === value.data_fim
}

function diasNoRange(value: { data_inicio: string; data_fim: string }): number {
  return differenceInDays(new Date(value.data_fim), new Date(value.data_inicio))
}

export default function PeriodoForm({ value, onChange, onBuscar, loading, presets }: Props) {
  const dias = diasNoRange(value)
  const dataFimMenor = !!(value.data_fim && value.data_inicio && new Date(value.data_fim) < new Date(value.data_inicio))
  const periodoInvalido = dias > MAX_BI_DAYS || dataFimMenor

  function handleBuscar() {
    if (periodoInvalido) return
    if (onBuscar) onBuscar()
  }

  const handlePreset = (novo: { data_inicio: string; data_fim: string }) => {
    const dias = diasNoRange(novo)
    const dataFimMenor = novo.data_fim && novo.data_inicio && new Date(novo.data_fim) < new Date(novo.data_inicio)
    if (dias > MAX_BI_DAYS || dataFimMenor) return
    onChange(novo)
    if (onBuscar) onBuscar(novo)
  }

  return (
    <div className="flex flex-col gap-3">
      {presets && (
        <div className="flex gap-1.5 flex-wrap">
          {presets.map((p) => {
            const ativo = presetAtivo(p, value)
            return (
              <button
                key={p.label}
                type="button"
                onClick={() => handlePreset(computePreset(p))}
                className={`text-xs px-2.5 py-1 rounded-full transition ${
                  ativo
                    ? 'bg-primary text-white shadow-sm'
                    : 'bg-bg-hover text-text-secondary hover:bg-primary-lighter hover:text-primary'
                }`}
              >
                {p.label}
              </button>
            )
          })}
        </div>
      )}
      <div className="flex flex-wrap gap-2 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-text-muted">De</label>
          <input
            type="date"
            className="form-input-base"
            value={value.data_inicio}
            onChange={(e) => onChange({ ...value, data_inicio: e.target.value })}
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-text-muted">Até</label>
          <input
            type="date"
            className="form-input-base"
            value={value.data_fim}
            onChange={(e) => onChange({ ...value, data_fim: e.target.value })}
          />
        </div>
        {onBuscar && (
          <button
            onClick={handleBuscar}
            disabled={loading || periodoInvalido}
            className="bg-primary hover:bg-primary-hover text-white font-semibold px-5 py-2 rounded-lg transition disabled:opacity-50 text-sm"
          >
            {loading ? 'Buscando...' : 'Buscar'}
          </button>
        )}
      </div>
      {periodoInvalido && (
        <p className="text-xs text-danger">
          {dataFimMenor
            ? "Data final não pode ser anterior à data inicial."
            : `Período máximo permitido é ${MAX_BI_DAYS} dias. Selecione um intervalo menor.`}
        </p>
      )}
    </div>
  )
}
