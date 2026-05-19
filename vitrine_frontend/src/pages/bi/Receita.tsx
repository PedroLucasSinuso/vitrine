import { useState, useCallback, useEffect, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { subMonths, startOfMonth, endOfMonth, format } from 'date-fns'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import BiTooltip from '../../components/bi/BiTooltip'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import Card from '../../components/ui/Card'
import SectionHeader from '../../components/ui/SectionHeader'
import { fetchReceita, fetchQuantidade, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { ItemDimensaoDTO, PeriodoBi, Dimensao, Metrica } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { CHART } from '../../utils/colors'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { BarChart3 } from 'lucide-react'
import Skeleton from '../../components/ui/Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'

const PRESETS_RECEITA: Preset[] = [
  { label: '7 dias', kind: 'days', days: 7 },
  { label: '30 dias', kind: 'days', days: 30 },
  { label: 'Este mês', kind: 'current_month' },
  { label: 'Mês passado', kind: 'last_month' },
]

function periodoInicial(): PeriodoBi {
  const mesPassado = subMonths(new Date(), 1)
  return {
    data_inicio: format(startOfMonth(mesPassado), 'yyyy-MM-dd'),
    data_fim: format(endOfMonth(mesPassado), 'yyyy-MM-dd'),
  }
}

function labelDimensao(item: ItemDimensaoDTO, dimensao: Dimensao): string {
  if (dimensao === 'produto') return item.produto ?? item.familia ?? item.grupo
  if (dimensao === 'familia') return item.familia ?? item.grupo
  return item.grupo
}

export default function Receita() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [dimensao, setDimensao] = useState<Dimensao>(
    (searchParams.get('dimensao') as Dimensao) ?? 'produto'
  )
  const [metrica, setMetrica] = useState<Metrica>(
    (searchParams.get('metrica') as Metrica) ?? 'receita_produto'
  )
  const [filtroGrupo, setFiltroGrupo] = useState('')
  const [filtroFamilia, setFiltroFamilia] = useState('')
  const [dados, setDados] = useState<ItemDimensaoDTO[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const navigate = useNavigate()
  const cache = useBiCache()
  const { toast } = useToast()

  const cacheKey = `receita_${dimensao}_${metrica}`

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    if (!force) {
      const cached = cache.get<ItemDimensaoDTO[]>(cacheKey, p)
      if (cached) { setDados(cached); return }
    }
    setErro(null)
    setLoading(true)
    try {
      const data = metrica === 'receita_produto'
        ? await fetchReceita(p, dimensao)
        : await fetchQuantidade(p, dimensao)
      setDados(data)
      cache.set(cacheKey, p, data)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [periodo, dimensao, metrica, cache]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.invalidate(cacheKey)
    buscar(periodoOverride, true)
  }

  function syncParams(d: Dimensao, m: Metrica) {
    const next = new URLSearchParams()
    if (d !== 'produto') next.set('dimensao', d)
    if (m !== 'receita_produto') next.set('metrica', m)
    setSearchParams(next, { replace: true })
  }

  const grupos = useMemo(() => {
    if (dimensao === 'grupo') return [] as string[]
    return [...new Set(dados.map(d => d.grupo))].sort()
  }, [dados, dimensao])

  const familias = useMemo(() => {
    if (!filtroGrupo || dimensao !== 'produto') return [] as string[]
    return [...new Set(dados.filter(d => d.grupo === filtroGrupo).map(d => d.familia).filter((f): f is string => f != null))].sort()
  }, [dados, filtroGrupo, dimensao])

  const dadosFiltrados = useMemo(() => {
    if (dimensao === 'grupo') return dados
    return dados.filter(d => {
      if (filtroGrupo && d.grupo !== filtroGrupo) return false
      if (filtroFamilia && d.familia !== filtroFamilia) return false
      return true
    })
  }, [dados, dimensao, filtroGrupo, filtroFamilia])

  const isReceita = metrica === 'receita_produto'
  const top10 = dadosFiltrados.slice(0, 10).map((item) => ({
    label: labelDimensao(item, dimensao),
    valor: item.valor,
  }))

  return (
    <BiPageLayout titulo="Receita por Dimensão" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Receita' }]}>
      <Card variant="bordered">
        <div className="flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_RECEITA} />
          <div className="flex gap-4 flex-wrap">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500 dark:text-slate-400">Dimensão</label>
              <select
                className="border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={dimensao}
                onChange={(e) => { const val = e.target.value as Dimensao; setDimensao(val); syncParams(val, metrica) }}
              >
                <option value="grupo">Grupo</option>
                <option value="familia">Família</option>
                <option value="produto">Produto</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-slate-500 dark:text-slate-400">Métrica</label>
              <select
                className="border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={metrica}
                onChange={(e) => { const val = e.target.value as Metrica; setMetrica(val); syncParams(dimensao, val) }}
              >
                <option value="receita_produto">Receita</option>
                <option value="qtd_item">Quantidade</option>
              </select>
            </div>
          </div>
          {dimensao !== 'grupo' && (
            <div className="flex gap-4 flex-wrap">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-slate-500 dark:text-slate-400">Grupo</label>
                <select
                  className="border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  value={filtroGrupo}
                  onChange={(e) => { setFiltroGrupo(e.target.value); setFiltroFamilia('') }}
                >
                  <option value="">Todos</option>
                  {grupos.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              {dimensao === 'produto' && filtroGrupo && (
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-slate-500 dark:text-slate-400">Família</label>
                  <select
                    className="border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    value={filtroFamilia}
                    onChange={(e) => setFiltroFamilia(e.target.value)}
                  >
                    <option value="">Todas</option>
                    {familias.map(f => <option key={f} value={f}>{f}</option>)}
                  </select>
                </div>
              )}
            </div>
          )}
          {erro && <ErrorBanner message={erro} />}
          <ExportButtons
            onExcel={() => { exportarExcelBI(periodo, metrica === 'receita_produto' ? 'receita' : 'quantidade', { dimensao }); toast({ type: 'success', message: 'Excel exportado' }) }}
            onCsv={() => { baixarCSVdeArray(dados, metrica === 'receita_produto' ? 'receita' : 'quantidade'); toast({ type: 'success', message: 'CSV exportado' }) }}
            disabled={dados.length === 0}
          />
        </div>
      </Card>

      {loading && !dados.length && (
        <Card variant="bordered">
          <Skeleton className="h-5 w-40 mb-4" />
          <Skeleton variant="chart" />
        </Card>
      )}
      {!loading && dados.length === 0 && (
        <EmptyState title="Nenhum dado no período" description="Tente ampliar o período ou alterar os filtros." />
      )}
      {dados.length > 0 && dadosFiltrados.length === 0 && (
        <EmptyState title="Nenhum resultado para os filtros" description="Tente limpar os filtros de grupo ou família." />
      )}
      {dados.length > 0 && dadosFiltrados.length > 0 && (
        <>
          <Card variant="bordered">
            <SectionHeader icon={BarChart3}>Top 10</SectionHeader>
            <div className="w-full aspect-[16/9] md:aspect-[21/9]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={top10} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
                <defs>
                  <linearGradient id="barGradientReceita" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor={CHART.green} stopOpacity={0.9} />
                    <stop offset="100%" stopColor={CHART.green} stopOpacity={0.25} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#9ca3af' }} tickFormatter={(v) => isReceita ? `${(v / 1000).toFixed(0)}k` : v} />
                <YAxis type="category" dataKey="label" width={120} tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip content={<BiTooltip />} />
                <Bar dataKey="valor" fill="url(#barGradientReceita)" radius={[0, 4, 4, 0]} animationBegin={0} animationDuration={600} />
              </BarChart>
            </ResponsiveContainer>
            </div>
          </Card>

          <Card variant="bordered">
            <SectionHeader>
              Todos os resultados <span className="text-slate-400 dark:text-slate-500 font-normal">({dadosFiltrados.length})</span>
            </SectionHeader>
            <div className="overflow-x-auto max-h-96 overflow-y-auto border border-slate-200 dark:border-slate-700/50 rounded-lg">
              <table className="w-full text-sm table-fixed">
                <thead>
                  <tr className="border-b dark:border-slate-700 text-left sticky top-0 bg-white dark:bg-slate-800 z-10">
                    <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium w-full">Grupo</th>
                    {dimensao !== 'grupo' && <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium w-full">Família</th>}
                    {dimensao === 'produto' && <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium w-full">Produto</th>}
                    <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium text-right w-28">
                      {isReceita ? 'Receita' : 'Quantidade'}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {dadosFiltrados.map((item, i) => (
                    <tr
                      key={i}
                      onClick={() => item.codigo && navigate(`/bi/sku?codigo=${item.codigo}`)}
                      className={`border-b dark:border-slate-700 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-700 ${item.codigo ? 'cursor-pointer' : ''}`}
                    >
                      <td className="py-2 text-slate-700 dark:text-slate-300 truncate" title={item.grupo}>{item.grupo}</td>
                      {dimensao !== 'grupo' && <td className="py-2 text-slate-500 dark:text-slate-400 truncate" title={item.familia ?? ''}>{item.familia ?? '\u2014'}</td>}
                      {dimensao === 'produto' && <td className="py-2 text-slate-700 dark:text-slate-300 truncate" title={item.produto ?? ''}>{item.produto ?? '\u2014'}</td>}
                      <td className="py-2 text-right font-semibold text-slate-800 dark:text-slate-100">
                        {isReceita ? formatCurrency(item.valor) : item.valor.toLocaleString('pt-BR')}
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
