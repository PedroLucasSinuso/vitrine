import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { subDays, format } from 'date-fns'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import Card from '../../components/ui/Card'
import SectionHeader from '../../components/ui/SectionHeader'
import KpiCard from '../../components/bi/KpiCard'
import { fetchTrocas, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { TrocasDTO, PeriodoBi } from '../../types'
import { formatCurrency, formatNumber } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { useCountUp } from '../../hooks/useCountUp'
import Skeleton from '../../components/ui/Skeleton'

const PRESETS_TROCAS: Preset[] = [
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

export default function Trocas() {
  const navigate = useNavigate()
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [dados, setDados] = useState<TrocasDTO | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const cache = useBiCache()
  const { toast } = useToast()

  const animTrocas = useCountUp(dados?.total_trocas ?? 0, 600, !!dados)
  const animTaxa = useCountUp(dados?.taxa_troca_pct ?? 0, 600, !!dados)

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    if (!force) {
      const cached = cache.get<TrocasDTO>('trocas', p)
      if (cached) { setDados(cached); return }
    }
    setErro(null)
    setLoading(true)
    try {
      const data = await fetchTrocas(p)
      setDados(data)
      cache.set('trocas', p, data)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [periodo, cache])

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.invalidate('trocas')
    buscar(periodoOverride, true)
  }

  return (
    <BiPageLayout titulo="Trocas" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Trocas' }]}>
      {/* Filters */}
      <Card variant="bordered">
        <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_TROCAS} />
        {erro && <div className="mt-3"><ErrorBanner message={erro} /></div>}
        <div className="mt-3">
          <ExportButtons
            onExcel={() => { exportarExcelBI(periodo, 'trocas'); toast({ type: 'success', message: 'Excel exportado' }) }}
            onCsv={() => { if (dados) { baixarCSVdeArray(dados.por_produto, 'trocas'); toast({ type: 'success', message: 'CSV exportado' }) } }}
            disabled={!dados}
          />
        </div>
      </Card>

      {/* Loading skeleton */}
      {loading && !dados && (
        <div className="grid grid-cols-2 gap-3">
          <Skeleton variant="kpi" />
          <Skeleton variant="kpi" />
        </div>
      )}

      {/* Empty state */}
      {!loading && !dados && !erro && (
        <EmptyState title="Nenhum dado no período" description="Tente ampliar o período." />
      )}

      {/* Data */}
      {dados && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <KpiCard label="Total de Trocas" valor={formatNumber(animTrocas)} />
            <KpiCard label="Taxa de Troca" valor={`${animTaxa.toFixed(2)}%`} />
          </div>

          <Card variant="bordered">
            <SectionHeader>
              Por produto <span className="text-slate-400 dark:text-slate-500 font-normal">({dados.por_produto.length})</span>
            </SectionHeader>
            {dados.por_produto.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-slate-500">Nenhuma troca no período.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm table-fixed">
                  <thead>
                    <tr className="border-b dark:border-slate-700 text-left">
                      <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium w-28">Código</th>
                      <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium w-full">Produto</th>
                      <th className="pb-2 text-xs text-slate-400 dark:text-slate-500 font-medium text-right w-28">Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                      {dados.por_produto.map((item, i) => (
                        <tr
                          key={i}
                          onClick={() => navigate(`/bi/sku?codigo=${item.codigo}`)}
                          className="border-b dark:border-slate-700 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer"
                        >
                          <td className="py-2 text-slate-400 dark:text-slate-500 font-mono truncate" title={item.codigo}>{item.codigo}</td>
                          <td className="py-2 text-slate-700 dark:text-slate-300 truncate" title={item.produto}>{item.produto}</td>
                          <td className="py-2 text-right font-semibold text-slate-800 dark:text-slate-100">{formatCurrency(item.receita)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </BiPageLayout>
  )
}
