import { useState, useCallback, useEffect } from 'react'
import { subDays, format } from 'date-fns'
import AdminHeader from '../../components/AdminHeader'
import BiSubNav from '../../components/bi/BiSubNav'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import { fetchTemporalHora, fetchTemporalDiaSemana, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { PontoHoraDTO, PontoDiaSemanaDTO, PeriodoBi, Metrica } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import Skeleton from '../../components/ui/Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'

const PRESETS_TEMPORAL: Preset[] = [
  { label: '7 dias', kind: 'days', days: 7 },
  { label: '30 dias', kind: 'days', days: 30 },
]

function periodoInicial(): PeriodoBi {
  return {
    data_inicio: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
    data_fim: format(new Date(), 'yyyy-MM-dd'),
  }
}

type Aba = 'hora' | 'dia_semana'

interface TooltipPayload {
  value: number
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayload[]; label?: string }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-900 text-white px-3 py-2 rounded-lg shadow-lg text-xs">
      <p className="font-semibold mb-1">{label}</p>
      <p>{formatCurrency(payload[0].value)}</p>
    </div>
  )
}

export default function Temporal() {
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [metrica, setMetrica] = useState<Metrica>('receita_produto')
  const [aba, setAba] = useState<Aba>('hora')
  const [porHora, setPorHora] = useState<PontoHoraDTO[]>([])
  const [porDia, setPorDia] = useState<PontoDiaSemanaDTO[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const cache = useBiCache()
  const { toast } = useToast()

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    const cacheKey = `temporal_${metrica}`
    if (!force) {
      const cached = cache.get<{ hora: PontoHoraDTO[]; dia: PontoDiaSemanaDTO[] }>(cacheKey, p)
      if (cached) { setPorHora(cached.hora); setPorDia(cached.dia); return }
    }
    setErro('')
    setLoading(true)
    try {
      const [hora, dia] = await Promise.all([
        fetchTemporalHora(p, metrica),
        fetchTemporalDiaSemana(p, metrica),
      ])
      setPorHora(hora)
      setPorDia(dia)
      cache.set(cacheKey, p, { hora, dia })
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [periodo, metrica, cache])

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps -- Mount-only fetch via setTimeout; deps intentionally omitted -- Mount-only fetch via setTimeout; deps intentionally omitted

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.clear()
    buscar(periodoOverride, true)
  }

  const isReceita = metrica === 'receita_produto'
  const dadosGrafico = aba === 'hora'
    ? porHora.map((d) => ({ label: `${d.hora}h`, valor: d.valor }))
    : porDia.map((d) => ({ label: d.dia_semana, valor: d.valor }))

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
      <AdminHeader titulo="Distribuição Temporal" paginaAtual="bi" hideNav breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Temporal' }]} />
      <BiSubNav />

      <div className="w-full max-w-4xl flex flex-col gap-5">

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_TEMPORAL} />
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400">Métrica</label>
            <select
              className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-40"
              value={metrica}
              onChange={(e) => setMetrica(e.target.value as Metrica)}
            >
              <option value="receita_produto">Receita</option>
              <option value="qtd_item">Quantidade</option>
            </select>
          </div>
          {erro && <p className="text-red-500 text-sm">{erro}</p>}
          <div className="flex gap-2">
            <button
              onClick={() => { exportarExcelBI(periodo, 'diario', { metrica }); toast({ type: 'success', message: 'Excel exportado' }) }}
              disabled={porHora.length === 0 && porDia.length === 0}
              className="text-xs bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
            >
              Excel
            </button>
            <button
              onClick={() => { baixarCSVdeArray(aba === 'hora' ? porHora : porDia, `temporal-${aba}`); toast({ type: 'success', message: 'CSV exportado' }) }}
              disabled={porHora.length === 0 && porDia.length === 0}
              className="text-xs bg-gray-600 hover:bg-gray-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
            >
              CSV
            </button>
          </div>
        </div>

        {loading && porHora.length === 0 && porDia.length === 0 && (
          <Skeleton className="h-[340px] rounded-2xl" />
        )}
        {(porHora.length > 0 || porDia.length > 0) && (
          <>
            <div className="flex gap-1 bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-1 w-fit">
              {([['hora', 'Por Hora'], ['dia_semana', 'Por Dia da Semana']] as [Aba, string][]).map(([a, label]) => (
                <button
                  key={a}
                  onClick={() => setAba(a)}
                  className={`px-5 py-2 rounded-xl text-sm font-semibold transition ${
                    aba === a ? 'bg-primary text-white' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
              <ResponsiveContainer width="100%" minHeight={280}>
                <BarChart data={dadosGrafico} margin={{ top: 0, right: 8, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#059669" stopOpacity={0.9} />
                      <stop offset="100%" stopColor="#059669" stopOpacity={0.3} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#9ca3af' }} />
                  <YAxis
                    tick={{ fontSize: 11, fill: '#9ca3af' }}
                    tickFormatter={(v) => isReceita ? `${(v / 1000).toFixed(0)}k` : v}
                    width={40}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="valor" fill="url(#barGradient)" radius={[4, 4, 0, 0]} animationBegin={0} animationDuration={600} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
