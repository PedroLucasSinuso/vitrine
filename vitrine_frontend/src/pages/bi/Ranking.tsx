import { useState, useCallback, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { subDays, format } from 'date-fns'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import EmptyState from '../../components/ui/EmptyState'
import { fetchRanking, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { ItemRankingDTO, PeriodoBi, Metrica } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import Skeleton from '../../components/ui/Skeleton'

const PRESETS_RANKING: Preset[] = [
  { label: '7 dias', kind: 'days', days: 7 },
  { label: '30 dias', kind: 'days', days: 30 },
  { label: 'Este mês', kind: 'current_month' },
  { label: 'Mês passado', kind: 'last_month' },
]

function periodoInicial(): PeriodoBi {
  return {
    data_inicio: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    data_fim: format(new Date(), 'yyyy-MM-dd'),
  }
}

export default function Ranking() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [metrica, setMetrica] = useState<Metrica>(
    (searchParams.get('metrica') as Metrica) ?? 'receita_produto'
  )
  const [top, setTop] = useState<number>(
    searchParams.get('top') ? Number(searchParams.get('top')) : 10
  )
  const [dados, setDados] = useState<ItemRankingDTO[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const cache = useBiCache()
  const { toast } = useToast()

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    const cacheKey = `ranking_${metrica}_${top}`
    if (!force) {
      const cached = cache.get<ItemRankingDTO[]>(cacheKey, p)
      if (cached) { setDados(cached); return }
    }
    setErro('')
    setLoading(true)
    try {
      const data = await fetchRanking(p, metrica, top)
      setDados(data)
      cache.set(cacheKey, p, data)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [periodo, metrica, top, cache])

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function syncParams(m: Metrica, t: number) {
    const next = new URLSearchParams()
    if (m !== 'receita_produto') next.set('metrica', m)
    if (t !== 10) next.set('top', String(t))
    setSearchParams(next, { replace: true })
  }

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.clear()
    buscar(periodoOverride, true)
  }

  const isReceita = metrica === 'receita_produto'
  const maximo = dados[0]?.valor ?? 1

  return (
    <BiPageLayout titulo="Ranking de Produtos" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Ranking' }]}>
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-4">
        <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_RANKING} />
        <div className="flex gap-4 flex-wrap">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400">Métrica</label>
            <select
              className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={metrica}
              onChange={(e) => { const val = e.target.value as Metrica; setMetrica(val); syncParams(val, top) }}
            >
              <option value="receita_produto">Receita</option>
              <option value="qtd_item">Quantidade</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400">Top</label>
            <select
              className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={top}
              onChange={(e) => { const val = Number(e.target.value); setTop(val); syncParams(metrica, val) }}
            >
              {[5, 10, 20, 50].map((n) => (
                <option key={n} value={n}>Top {n}</option>
              ))}
            </select>
          </div>
        </div>
        {erro && <p className="text-red-500 text-sm">{erro}</p>}
        <ExportButtons
          onExcel={() => { exportarExcelBI(periodo, 'ranking', { metrica, top }); toast({ type: 'success', message: 'Excel exportado' }) }}
          onCsv={() => { baixarCSVdeArray(dados, 'ranking'); toast({ type: 'success', message: 'CSV exportado' }) }}
          disabled={dados.length === 0}
        />
      </div>

      {loading && !dados.length && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
          <Skeleton className="h-5 w-48 mb-4" />
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full mb-2" />
          ))}
        </div>
      )}
      {!loading && dados.length === 0 && (
        <EmptyState title="Nenhum dado no período" description="Tente ampliar o período ou alterar os filtros." />
      )}
      {dados.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
          <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">
            Top {dados.length} — {isReceita ? 'Receita' : 'Quantidade'}
          </h2>
          <div className="flex flex-col gap-3">
            {dados.map((item, i) => (
              <div key={item.codigo} className="flex flex-col gap-1">
                <div className="flex justify-between items-baseline">
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    <span className="text-gray-400 dark:text-gray-500 mr-2">{i + 1}.</span>
                    {item.produto}
                  </span>
                  <span className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                    {isReceita ? formatCurrency(item.valor) : item.valor.toLocaleString('pt-BR')}
                  </span>
                </div>
                <div className="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all"
                    style={{ width: `${(item.valor / maximo) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </BiPageLayout>
  )
}
