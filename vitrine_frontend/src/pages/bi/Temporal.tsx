import { useState, useCallback, useEffect } from 'react'
import { subDays, format } from 'date-fns'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import BiTooltip from '../../components/bi/BiTooltip'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import Card from '../../components/ui/Card'
import { fetchTemporalHora, fetchTemporalDiaSemana, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { PontoHoraDTO, PontoDiaSemanaDTO, PeriodoBi, Metrica } from '../../types'
import { CHART } from '../../utils/colors'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { Clock } from 'lucide-react'
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

export default function Temporal() {
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [metrica, setMetrica] = useState<Metrica>('receita_produto')
  const [aba, setAba] = useState<Aba>('hora')
  const [porHora, setPorHora] = useState<PontoHoraDTO[]>([])
  const [porDia, setPorDia] = useState<PontoDiaSemanaDTO[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const cache = useBiCache()
  const { toast } = useToast()

  const cacheKey = `temporal_${metrica}`

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    if (!force) {
      const cached = cache.get<{ hora: PontoHoraDTO[]; dia: PontoDiaSemanaDTO[] }>(cacheKey, p)
      if (cached) { setPorHora(cached.hora); setPorDia(cached.dia); return }
    }
    setErro(null)
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
  }, [periodo, metrica, cache]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.invalidate(cacheKey)
    buscar(periodoOverride, true)
  }

  const isReceita = metrica === 'receita_produto'
  const temDados = porHora.length > 0 || porDia.length > 0
  const dadosGrafico = aba === 'hora'
    ? porHora.map((d) => ({ label: `${d.hora}h`, valor: d.valor }))
    : porDia.map((d) => ({ label: d.dia_semana, valor: d.valor }))

  return (
    <BiPageLayout titulo="Distribuição Temporal" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Temporal' }]}>
      <Card variant="bordered">
        <div className="flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_TEMPORAL} />
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500 dark:text-slate-400">Métrica</label>
            <select
              className="border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-40"
              value={metrica}
              onChange={(e) => setMetrica(e.target.value as Metrica)}
            >
              <option value="receita_produto">Receita</option>
              <option value="qtd_item">Quantidade</option>
            </select>
          </div>
          {erro && <ErrorBanner message={erro} />}
          <ExportButtons
            onExcel={() => { exportarExcelBI(periodo, 'diario', { metrica }); toast({ type: 'success', message: 'Excel exportado' }) }}
            onCsv={() => { baixarCSVdeArray(aba === 'hora' ? porHora : porDia, `temporal-${aba}`); toast({ type: 'success', message: 'CSV exportado' }) }}
            disabled={!temDados}
          />
        </div>
      </Card>

      {loading && !temDados && (
        <Card variant="bordered">
          <Skeleton className="h-5 w-40 mb-4" />
          <Skeleton variant="chart" />
        </Card>
      )}
      {!loading && !temDados && (
        <EmptyState title="Nenhum dado no período" description="Tente ampliar o período ou alterar os filtros." />
      )}
      {temDados && (
        <>
          <div className="flex gap-1 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-1 w-fit">
            {([['hora', 'Por Hora'], ['dia_semana', 'Por Dia da Semana']] as [Aba, string][]).map(([a, label]) => (
              <button
                key={a}
                onClick={() => setAba(a)}
                className={`px-5 py-2 rounded-xl text-sm font-semibold transition relative ${
                  aba === a ? 'bg-primary text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <Card variant="bordered">
            <div className="flex items-center gap-2 mb-4">
              <Clock size={16} className="text-primary" />
              <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                {aba === 'hora' ? 'Por Hora' : 'Por Dia da Semana'}
              </h2>
            </div>
            <div className="w-full aspect-[16/9] md:aspect-[21/9]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dadosGrafico} margin={{ top: 0, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="barGradientTemporal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={isReceita ? CHART.green : CHART.amber} stopOpacity={0.9} />
                    <stop offset="100%" stopColor={isReceita ? CHART.green : CHART.amber} stopOpacity={0.25} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#9ca3af' }} />
                <YAxis
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  tickFormatter={(v) => isReceita ? `R$ ${(v / 1000).toFixed(0)}k` : `${(v / 1000).toFixed(0)}k un.`}
                  width={40}
                />
                <Tooltip content={<BiTooltip />} />
                <Bar dataKey="valor" fill="url(#barGradientTemporal)" radius={[4, 4, 0, 0]} animationBegin={0} animationDuration={600} />
              </BarChart>
            </ResponsiveContainer>
            </div>
          </Card>
        </>
      )}
    </BiPageLayout>
  )
}
