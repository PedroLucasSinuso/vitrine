import { useState, useCallback, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { subDays, format, parseISO, getDay } from 'date-fns'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import BiTooltip from '../../components/bi/BiTooltip'
import EmptyState from '../../components/ui/EmptyState'
import KpiCard from '../../components/bi/KpiCard'
import { fetchSku, exportarExcelBI } from '../../api/bi'
import { buscarProdutosPorNome } from '../../api/produtos'
import { baixarCSVdeArray } from '../../utils/csv'
import type { SkuDTO, PeriodoBi, ProdutoBasico } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import Skeleton from '../../components/ui/Skeleton'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
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
  const [searchParams] = useSearchParams()
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [codigo, setCodigo] = useState('')
  const codigoRef = useRef(codigo)
  useEffect(() => { codigoRef.current = codigo }, [codigo])
  const [dados, setDados] = useState<SkuDTO | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<ProdutoBasico[]>([])
  const [produtoNome, setProdutoNome] = useState('')
  const searchTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const cache = useBiCache()
  const { toast } = useToast()

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
    setErro('')
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

  useEffect(() => {
    const codigoParam = searchParams.get('codigo')
    if (codigoParam) {
      setCodigo(codigoParam)
      buscar(codigoParam)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.clear()
    buscar(undefined, periodoOverride, true)
  }

  return (
    <BiPageLayout titulo="Análise de SKU" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'SKU' }]}>
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-4">
        <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_SKU} />
        <div>
          <input
            className="w-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Buscar produto por nome..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchResults.length > 0 && (
            <div className="mt-1 bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 divide-y divide-gray-100 dark:divide-gray-700 max-h-48 overflow-y-auto">
              {searchResults.map((p) => (
                <button
                  key={p.codigo_chamada}
                  onClick={() => {
                    setCodigo(p.codigo_chamada)
                    setProdutoNome(p.nome)
                    setSearchQuery('')
                    setSearchResults([])
                    buscar(p.codigo_chamada)
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-primary-lighter dark:hover:bg-gray-700 transition text-sm flex justify-between items-center"
                >
                  <span className="font-medium text-gray-800 dark:text-gray-100">{p.nome}</span>
                  <span className="text-gray-400 dark:text-gray-500 text-xs">{p.codigo_chamada}</span>
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
            className="flex-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="Código do produto (EAN ou PLU)"
            value={codigo}
            onChange={(e) => setCodigo(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && buscar(codigo)}
          />
          <button
            onClick={() => buscar()}
            disabled={loading}
            className="bg-primary hover:bg-primary-hover text-white font-semibold px-4 py-2 rounded-lg transition disabled:opacity-50 text-sm"
          >
            {loading ? '...' : 'Buscar'}
          </button>
        </div>
        {erro && <p className="text-red-500 text-sm">{erro}</p>}
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

      {loading && !dados && (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-24 rounded-2xl" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-2xl" />
            ))}
          </div>
        </div>
      )}
      {!loading && !dados && !erro && (
        <EmptyState title="Busque um produto" description="Digite o nome ou código de um produto para analisar." />
      )}
      {dados && (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
            <p className="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">{dados.grupo} · {dados.familia}</p>
            <p className="text-xl font-bold text-gray-800 dark:text-gray-100">{dados.produto}</p>
            <p className="text-sm text-gray-400 dark:text-gray-500 font-mono mt-1">{dados.codigo}</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiCard label="Receita Total" valor={formatCurrency(dados.receita_total)} destaque />
            <KpiCard label="Qtd. Vendida" valor={dados.qtd_total.toLocaleString('pt-BR')} />
            <KpiCard label="Tickets" valor={dados.qtd_tickets.toLocaleString('pt-BR')} />
            <KpiCard label="Ticket Médio" valor={formatCurrency(dados.ticket_medio)} />
          </div>

          {dados.ranking_dias.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Receita diária</h2>
              <ResponsiveContainer width="100%" minHeight={200}>
                <LineChart
                  data={dados.ranking_dias.slice().sort((a, b) => a.data.localeCompare(b.data))}
                  margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="data" tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => v.slice(5)} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} width={36} />
                  <Tooltip content={<BiTooltip />} labelFormatter={(l) => `Data: ${l}`} />
                  <Line type="monotone" dataKey="valor" stroke="#059669" strokeWidth={2} dot={false} animationBegin={0} animationDuration={600} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {dados.distribuicao_hora.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Receita por hora</h2>
              <ResponsiveContainer width="100%" minHeight={180}>
                <BarChart data={dados.distribuicao_hora.map((d) => ({ label: `${d.hora}h`, valor: d.valor }))} margin={{ top: 0, right: 8, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#059669" stopOpacity={0.9} />
                      <stop offset="100%" stopColor="#059669" stopOpacity={0.3} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} width={36} />
                  <Tooltip content={<BiTooltip />} />
                  <Bar dataKey="valor" fill="url(#barGradient)" radius={[4, 4, 0, 0]} animationBegin={0} animationDuration={600} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {dados.ranking_dias.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Receita por dia da semana</h2>
              <ResponsiveContainer width="100%" minHeight={180}>
                <BarChart
                  data={(() => {
                    const dias = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
                    const agrupado = Array(7).fill(0)
                    dados.ranking_dias.forEach((d) => {
                      agrupado[getDay(parseISO(d.data))] += d.valor
                    })
                    return dias.map((label, i) => ({ label, valor: agrupado[i] }))
                  })()}
                  margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#059669" stopOpacity={0.9} />
                      <stop offset="100%" stopColor="#059669" stopOpacity={0.3} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} width={36} />
                  <Tooltip content={<BiTooltip />} />
                  <Bar dataKey="valor" fill="url(#barGradient)" radius={[4, 4, 0, 0]} animationBegin={0} animationDuration={600} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
            <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Top dias de venda</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b dark:border-gray-700 text-left">
                  <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium">#</th>
                  <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium">Data</th>
                  <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium text-right">Receita</th>
                </tr>
              </thead>
              <tbody>
                {dados.ranking_dias.map((item, i) => (
                  <tr key={i} className="border-b dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="py-2 text-gray-400 dark:text-gray-500">{i + 1}</td>
                    <td className="py-2 text-gray-700 dark:text-gray-300">{item.data}</td>
                    <td className="py-2 text-right font-semibold text-gray-800 dark:text-gray-100">{formatCurrency(item.valor)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </BiPageLayout>
  )
}
