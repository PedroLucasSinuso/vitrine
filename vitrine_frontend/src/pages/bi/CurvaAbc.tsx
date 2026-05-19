import { useState, useCallback, useEffect, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { subDays, format } from 'date-fns'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import Card from '../../components/ui/Card'
import SectionHeader from '../../components/ui/SectionHeader'
import { fetchCurvaAbc, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { ItemCurvaAbcDTO, PeriodoBi, Dimensao, CurvaAbc } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { CURVA_CORES } from '../../utils/colors'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { PieChart as PieChartIcon } from 'lucide-react'
import Skeleton from '../../components/ui/Skeleton'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const PRESETS_CURVA: Preset[] = [
  { label: '30 dias', kind: 'days', days: 30 },
  { label: '60 dias', kind: 'days', days: 60 },
  { label: '3 meses', kind: 'days', days: 90 },
  { label: 'Este mês', kind: 'current_month' },
]

function periodoInicial(): PeriodoBi {
  return {
    data_inicio: format(subDays(new Date(), 90), 'yyyy-MM-dd'),
    data_fim: format(new Date(), 'yyyy-MM-dd'),
  }
}

const CURVA_BADGE: Record<CurvaAbc, string> = {
  A: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  B: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  C: 'bg-slate-100 text-slate-700 dark:bg-slate-600 dark:text-slate-200',
}

export default function CurvaAbc() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [dimensao, setDimensao] = useState<Dimensao>(
    (searchParams.get('dimensao') as Dimensao) ?? 'produto'
  )
  const [dados, setDados] = useState<ItemCurvaAbcDTO[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const navigate = useNavigate()
  const cache = useBiCache()
  const { toast } = useToast()

  const cacheKey = `curva-abc_${dimensao}`

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    if (!force) {
      const cached = cache.get<ItemCurvaAbcDTO[]>(cacheKey, p)
      if (cached) { setDados(cached); return }
    }
    setErro(null)
    setLoading(true)
    try {
      const data = await fetchCurvaAbc(p, dimensao)
      setDados(data)
      cache.set(cacheKey, p, data)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [periodo, dimensao, cache]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function syncParams(d: Dimensao) {
    const next = new URLSearchParams()
    if (d !== 'produto') next.set('dimensao', d)
    setSearchParams(next, { replace: true })
  }

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.invalidate(cacheKey)
    buscar(periodoOverride, true)
  }

  const statsPorCurva = useMemo(() => {
    const totalReceita = dados.reduce((s, d) => s + d.receita, 0)
    const curvas = { A: { qtd: 0, receita: 0 }, B: { qtd: 0, receita: 0 }, C: { qtd: 0, receita: 0 } } as Record<CurvaAbc, { qtd: number; receita: number }>
    dados.forEach((d) => {
      curvas[d.curva].qtd++
      curvas[d.curva].receita += d.receita
    })
    return (Object.entries(curvas) as [CurvaAbc, { qtd: number; receita: number }][]).map(([curva, info]) => ({
      curva,
      ...info,
      pctReceita: totalReceita > 0 ? (info.receita / totalReceita) * 100 : 0,
    }))
  }, [dados])

  const pieData = statsPorCurva.map((s) => ({
    name: `Curva ${s.curva}`,
    value: s.receita,
  }))

  return (
    <BiPageLayout titulo="Curva ABC" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Curva ABC' }]}>
      <Card variant="bordered">
        <div className="flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_CURVA} />
          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-500 dark:text-slate-400">Dimensão</label>
            <select
              className="border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-40"
              value={dimensao}
              onChange={(e) => { const val = e.target.value as Dimensao; setDimensao(val); syncParams(val) }}
            >
              <option value="produto">Produto</option>
              <option value="familia">Família</option>
              <option value="grupo">Grupo</option>
            </select>
          </div>
          {erro && <ErrorBanner message={erro} />}
          <ExportButtons
            onExcel={() => { exportarExcelBI(periodo, 'curva-abc', { dimensao }); toast({ type: 'success', message: 'Excel exportado' }) }}
            onCsv={() => { baixarCSVdeArray(dados, 'curva-abc'); toast({ type: 'success', message: 'CSV exportado' }) }}
            disabled={dados.length === 0}
          />
        </div>
      </Card>

      {loading && !dados.length && (
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} variant="kpi" />
          ))}
        </div>
      )}
      {!loading && dados.length === 0 && (
        <EmptyState title="Nenhum dado no período" description="Tente ampliar o período ou alterar os filtros." />
      )}
      {dados.length > 0 && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {statsPorCurva.map(({ curva, qtd, receita, pctReceita }) => (
              <Card key={curva} variant="bordered" className="flex flex-col items-center text-center gap-1 p-4">
                <span className={`text-xs font-semibold px-2 py-1 rounded-full ${CURVA_BADGE[curva]}`}>
                  Curva {curva}
                </span>
                <p className="text-xl font-bold text-slate-800 dark:text-slate-100 break-words">{qtd}</p>
                <p className="text-xs text-slate-400 dark:text-slate-500">itens</p>
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-1">{formatCurrency(receita)}</p>
                <p className="text-xs text-slate-400 dark:text-slate-500">{pctReceita.toFixed(1)}% da receita</p>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card variant="bordered">
              <SectionHeader icon={PieChartIcon}>Distribuição da Receita</SectionHeader>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                    animationBegin={0}
                    animationDuration={600}
                  >
                    {pieData.map((_, idx) => (
                      <Cell key={idx} fill={CURVA_CORES[statsPorCurva[idx].curva]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-4 mt-2">
                {statsPorCurva.map(({ curva, pctReceita }) => (
                  <div key={curva} className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CURVA_CORES[curva] }} />
                    {curva} · {pctReceita.toFixed(1)}%
                  </div>
                ))}
              </div>
            </Card>

            <Card variant="bordered">
              <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">Concentração Acumulada</h2>
              <p className="text-3xl font-bold text-slate-800 dark:text-slate-100">
                {statsPorCurva[0]?.pctReceita.toFixed(1) ?? 0}%
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                da receita está em {statsPorCurva[0]?.qtd ?? 0} itens da Curva A
              </p>
              {/* Visual gauge */}
              <div className="mt-4 h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary to-primary-light rounded-full transition-all duration-700"
                  style={{ width: `${statsPorCurva[0]?.pctReceita ?? 0}%` }}
                />
              </div>
              <div className="mt-3 flex flex-col gap-1 text-sm text-slate-600 dark:text-slate-400">
                <p>· Curva A: {statsPorCurva[0]?.qtd ?? 0} itens · {statsPorCurva[0]?.pctReceita.toFixed(1) ?? 0}% receita</p>
                <p>· Curva B: {statsPorCurva[1]?.qtd ?? 0} itens · {statsPorCurva[1]?.pctReceita.toFixed(1) ?? 0}% receita</p>
                <p>· Curva C: {statsPorCurva[2]?.qtd ?? 0} itens · {statsPorCurva[2]?.pctReceita.toFixed(1) ?? 0}% receita</p>
              </div>
            </Card>
          </div>

          <Card variant="bordered">
            <SectionHeader>
              Classificação completa <span className="text-slate-400 dark:text-slate-500 font-normal">({dados.length})</span>
            </SectionHeader>
            <div className="overflow-x-auto max-h-96 overflow-y-auto border border-slate-200 dark:border-slate-700/50 rounded-lg">
              <table className="w-full text-sm table-fixed">
                <thead>
                  <tr className="border-b dark:border-slate-700 text-left sticky top-0 bg-white dark:bg-slate-800 z-10">
                    <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium w-8">#</th>
                    <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium">Grupo</th>
                    {dimensao !== 'grupo' && <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium">Família</th>}
                    {dimensao === 'produto' && <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium">Produto</th>}
                    <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium text-right w-24">Receita</th>
                    <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium text-right w-20">Part. %</th>
                    <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium text-right w-20">Acum. %</th>
                    <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium text-center w-16">Curva</th>
                  </tr>
                </thead>
                <tbody>
                  {dados.map((item, i) => (
                    <tr
                      key={i}
                      onClick={() => item.codigo && navigate(`/bi/sku?codigo=${item.codigo}`)}
                      className={`border-b dark:border-slate-700 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-700 ${item.codigo ? 'cursor-pointer' : ''}`}
                    >
                      <td className="py-2 text-slate-400 dark:text-slate-500">{i + 1}</td>
                      <td className="py-2 text-slate-700 dark:text-slate-300 truncate" title={item.grupo}>{item.grupo}</td>
                      {dimensao !== 'grupo' && <td className="py-2 text-slate-500 dark:text-slate-400 truncate" title={item.familia ?? ''}>{item.familia ?? '\u2014'}</td>}
                      {dimensao === 'produto' && <td className="py-2 text-slate-700 dark:text-slate-300 truncate" title={item.produto ?? ''}>{item.produto ?? '\u2014'}</td>}
                      <td className="py-2 text-right font-semibold text-slate-800 dark:text-slate-100">{formatCurrency(item.receita)}</td>
                      <td className="py-2 text-right text-slate-600 dark:text-slate-400">{item.participacao_pct.toFixed(2)}%</td>
                      <td className="py-2 text-right text-slate-600 dark:text-slate-400">{item.participacao_acumulada.toFixed(2)}%</td>
                      <td className="py-2 text-center">
                        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${CURVA_BADGE[item.curva]}`}>
                          {item.curva}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </BiPageLayout>
  )
}
