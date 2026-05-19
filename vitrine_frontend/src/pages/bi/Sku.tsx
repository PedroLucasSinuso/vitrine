import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { subDays, format } from 'date-fns'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import BiTooltip from '../../components/bi/BiTooltip'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import Card from '../../components/ui/Card'
import SectionHeader from '../../components/ui/SectionHeader'
import KpiCard from '../../components/bi/KpiCard'
import { fetchSku, exportarExcelBI } from '../../api/bi'
import { buscarProdutosPorNome } from '../../api/produtos'
import { baixarCSVdeArray } from '../../utils/csv'
import type { SkuDTO, PeriodoBi, ProdutoBasico } from '../../types'
import { formatCurrency, formatDateWithWeekday } from '../../utils/formatters'
import { CHART } from '../../utils/colors'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { useCountUp } from '../../hooks/useCountUp'
import { Search, TrendingUp, BarChart3, Calendar, Crown } from 'lucide-react'
import Skeleton from '../../components/ui/Skeleton'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid,
} from 'recharts'

const PRESETS_SKU: Preset[] = [
  { label: '7 dias', kind: 'days', days: 7 },
  { label: '30 dias', kind: 'days', days: 30 },
  { label: 'Este mês', kind: 'current_month' },
]

function periodoInicial(): PeriodoBi {
  return {
    data_inicio: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    data_fim: format(new Date(), 'yyyy-MM-dd'),
  }
}

export default function Sku() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [codigo, setCodigo] = useState(searchParams.get('codigo') ?? '')
  const codigoRef = useRef(codigo)
  useEffect(() => { codigoRef.current = codigo }, [codigo])
  const [dados, setDados] = useState<SkuDTO | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<ProdutoBasico[]>([])
  const [produtoNome, setProdutoNome] = useState('')
  const searchTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const cache = useBiCache()
  const { toast } = useToast()

  const animReceita = useCountUp(dados?.receita_total ?? 0, 600, !!dados)
  const animQtd = useCountUp(dados?.qtd_total ?? 0, 600, !!dados)
  const animTickets = useCountUp(dados?.qtd_tickets ?? 0, 600, !!dados)
  const animTicketMedio = useCountUp(dados?.ticket_medio ?? 0, 600, !!dados)

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current)
    const q = searchQuery.trim()
    searchTimer.current = setTimeout(async () => {
      if (q.length < 2) { setSearchResults([]); return }
      try {
        const data = await buscarProdutosPorNome(q)
        setSearchResults(data)
      } catch { setSearchResults([]) }
    }, 300)
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current) }
  }, [searchQuery])

  const buscar = useCallback(async (codigoParam?: string, periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    const valor = (codigoParam ?? codigoRef.current).trim()
    if (!valor) return
    const cacheKey = `sku_${valor}`
    if (!force) {
      const cached = cache.get<SkuDTO>(cacheKey, p)
      if (cached) { setDados(cached); return }
    }
    setErro(null)
    setLoading(true)
    try {
      const data = await fetchSku(p, valor)
      setDados(data)
      cache.set(cacheKey, p, data)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number } }
      if (err.response?.status === 400) setErro('Código inválido.')
      else if (err.response?.status === 404) setErro('Produto não encontrado no período informado.')
      else setErro('Erro ao carregar dados.')
      setDados(null)
    } finally {
      setLoading(false)
    }
  }, [periodo, cache])

  // React to URL ?codigo= changes — enables navigation between SKUs
  useEffect(() => {
    const codigoParam = searchParams.get('codigo')
    if (codigoParam && codigoParam !== codigoRef.current) {
      setCodigo(codigoParam)
      buscar(codigoParam)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Only react to URL param changes
  }, [searchParams.get('codigo')])

  function handleBuscar(periodoOverride?: PeriodoBi) {
    const valor = codigoRef.current.trim()
    if (valor) cache.invalidate(`sku_${valor}`)
    buscar(undefined, periodoOverride, true)
  }

  return (
    <BiPageLayout titulo="Análise de SKU" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'SKU' }]}>
      <Card variant="bordered">
        <div className="flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_SKU} />
          <div>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                className="w-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Buscar produto por nome..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            {searchResults.length > 0 && (
              <div className="mt-1 bg-white dark:bg-slate-800 rounded-lg shadow-md border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700 max-h-48 overflow-y-auto absolute left-0 right-0 z-20">
                {searchResults.map((p) => (
                  <button
                    key={p.codigo_chamada}
                    onClick={() => {
                      setCodigo(p.codigo_chamada)
                      setProdutoNome(p.nome)
                      setSearchQuery('')
                      setSearchResults([])
                      setSearchParams({ codigo: p.codigo_chamada })
                      buscar(p.codigo_chamada)
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-primary-lighter dark:hover:bg-slate-700 transition text-sm flex justify-between items-center"
                  >
                    <span className="font-medium text-slate-800 dark:text-slate-100">{p.nome}</span>
                    <span className="text-slate-400 dark:text-slate-500 text-xs">{p.codigo_chamada}</span>
                  </button>
                ))}
              </div>
            )}
            {produtoNome && !searchQuery && (
              <p className="mt-1 text-sm text-primary font-medium">{produtoNome}</p>
            )}
          </div>
          <div className="flex gap-2">
            <input
              className="flex-1 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Código do produto (EAN ou PLU)"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  setSearchParams({ codigo })
                  buscar(codigo)
                }
              }}
            />
            <button
              onClick={() => {
                setSearchParams({ codigo })
                buscar()
              }}
              disabled={loading}
              className="bg-primary hover:bg-primary-hover text-white font-semibold px-4 py-2 rounded-lg transition disabled:opacity-50 text-sm"
            >
              {loading ? '...' : 'Buscar'}
            </button>
          </div>
          {erro && <ErrorBanner message={erro} />}
          <ExportButtons
            onExcel={() => { exportarExcelBI(periodo, 'sku', { codigo }); toast({ type: 'success', message: 'Excel exportado' }) }}
            onCsv={() => {
              if (!dados) return
              const linhas = dados.ranking_dias.map((d) => ({ data: d.data, receita: d.valor }))
              baixarCSVdeArray(linhas, 'sku')
              toast({ type: 'success', message: 'CSV exportado' })
            }}
            disabled={!dados}
          />
        </div>
      </Card>

      {loading && !dados && (
        <div className="flex flex-col gap-4">
          <Skeleton variant="kpi" className="h-28" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} variant="kpi" />
            ))}
          </div>
        </div>
      )}
      {!loading && !dados && !erro && (
        <EmptyState title="Busque um produto" description="Digite o nome ou código de um produto para analisar." />
      )}
      {dados && (
        <>
          <div className="flex flex-col gap-3">
          <Card variant="bordered">
            <p className="text-xs text-slate-400 dark:text-slate-500 font-medium mb-1">{dados.grupo} · {dados.familia}</p>
            <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{dados.produto}</p>
            <p className="text-sm text-slate-400 dark:text-slate-500 font-mono mt-1">{dados.codigo}</p>
          </Card>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiCard label="Receita Total" valor={formatCurrency(animReceita)} />
            <KpiCard label="Qtd. Vendida" valor={animQtd.toLocaleString('pt-BR')} />
            <KpiCard label="Tickets" valor={animTickets.toLocaleString('pt-BR')} />
            <KpiCard label="Ticket Médio" valor={formatCurrency(animTicketMedio)} />
          </div>
          </div>

          {dados.ranking_dias.length > 0 && (
            <Card variant="bordered">
              <SectionHeader icon={TrendingUp}>Receita diária</SectionHeader>
              <div className="w-full aspect-[16/9] md:aspect-[21/9]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={dados.ranking_dias.slice().sort((a, b) => a.data.localeCompare(b.data))}
                  margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="areaGradientSku" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={CHART.green} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={CHART.green} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="data" tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => v.slice(5)} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} width={36} />
                  <Tooltip content={<BiTooltip />} labelFormatter={(l) => `Data: ${l}`} />
                  <Area type="monotone" dataKey="valor" stroke={CHART.green} strokeWidth={2} fill="url(#areaGradientSku)" animationBegin={0} animationDuration={600} />
                </AreaChart>
              </ResponsiveContainer>
              </div>
            </Card>
          )}

          {dados.distribuicao_hora.length > 0 && (
            <Card variant="bordered">
              <SectionHeader icon={BarChart3}>Receita por hora</SectionHeader>
              <div className="w-full aspect-[16/9] md:aspect-[21/9]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dados.distribuicao_hora.map((d) => ({ label: `${d.hora}h`, valor: d.valor }))} margin={{ top: 0, right: 8, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="barGradientSkuHora" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={CHART.green} stopOpacity={0.9} />
                      <stop offset="100%" stopColor={CHART.green} stopOpacity={0.25} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} width={36} />
                  <Tooltip content={<BiTooltip />} />
                  <Bar dataKey="valor" fill="url(#barGradientSkuHora)" radius={[4, 4, 0, 0]} animationBegin={0} animationDuration={600} />
                </BarChart>
              </ResponsiveContainer>
              </div>
            </Card>
          )}

          {dados.distribuicao_dia_semana.length > 0 && (
            <Card variant="bordered">
              <SectionHeader icon={Calendar}>Receita por dia da semana</SectionHeader>
              <div className="w-full aspect-[16/9] md:aspect-[21/9]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={dados.distribuicao_dia_semana.map((d) => ({ label: d.dia_semana, valor: d.valor }))}
                  margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="barGradientSkuDia" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={CHART.green} stopOpacity={0.9} />
                      <stop offset="100%" stopColor={CHART.green} stopOpacity={0.25} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} width={36} />
                  <Tooltip content={<BiTooltip />} />
                  <Bar dataKey="valor" fill="url(#barGradientSkuDia)" radius={[4, 4, 0, 0]} animationBegin={0} animationDuration={600} />
                </BarChart>
              </ResponsiveContainer>
              </div>
            </Card>
          )}

          <Card variant="bordered">
            <SectionHeader icon={Crown}>Top dias de venda</SectionHeader>
            <div className="overflow-x-auto max-h-64 overflow-y-auto">
              <table className="w-full text-sm">
              <thead>
                <tr className="border-b dark:border-slate-700 text-left">
                  <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium">#</th>
                  <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium">Data</th>
                  <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium text-right">Receita</th>
                </tr>
              </thead>
              <tbody>
                {dados.ranking_dias.map((item, i) => (
                  <tr key={i} className="border-b dark:border-slate-700 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-700">
                    <td className="py-2 text-slate-400 dark:text-slate-500">{i + 1}</td>
                    <td className="py-2 text-slate-700 dark:text-slate-300">{formatDateWithWeekday(item.data)}</td>
                    <td className="py-2 text-right font-semibold text-slate-800 dark:text-slate-100">{formatCurrency(item.valor)}</td>
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
