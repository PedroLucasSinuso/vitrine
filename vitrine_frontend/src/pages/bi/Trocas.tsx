import { useState, useCallback, useEffect } from 'react'
import { subDays, format } from 'date-fns'
import AdminHeader from '../../components/AdminHeader'
import BiSubNav from '../../components/bi/BiSubNav'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import KpiCard from '../../components/bi/KpiCard'
import { fetchTrocas, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { TrocasDTO, PeriodoBi } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
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
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [dados, setDados] = useState<TrocasDTO | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const cache = useBiCache()
  const { toast } = useToast()

  const buscar = useCallback(async (force = false) => {
    if (!force) {
      const cached = cache.get<TrocasDTO>('trocas', periodo)
      if (cached) { setDados(cached); return }
    }
    setErro('')
    setLoading(true)
    try {
      const data = await fetchTrocas(periodo)
      setDados(data)
      cache.set('trocas', periodo, data)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [periodo, cache])

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps -- Mount-only fetch via setTimeout; deps intentionally omitted -- Mount-only fetch via setTimeout; deps intentionally omitted

  function handleBuscar() {
    cache.clear()
    buscar(true)
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
      <AdminHeader titulo="Trocas" paginaAtual="bi" hideNav breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Trocas' }]} />
      <BiSubNav />

      <div className="w-full max-w-3xl flex flex-col gap-5">

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_TROCAS} />
          {erro && <p className="text-red-500 text-sm mt-3">{erro}</p>}
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => { exportarExcelBI(periodo, 'trocas'); toast({ type: 'success', message: 'Excel exportado' }) }}
              disabled={!dados}
              className="text-xs bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
            >
              Excel
            </button>
            <button
              onClick={() => { if (dados) { baixarCSVdeArray(dados.por_produto, 'trocas'); toast({ type: 'success', message: 'CSV exportado' }) } }}
              disabled={!dados}
              className="text-xs bg-gray-600 hover:bg-gray-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
            >
              CSV
            </button>
          </div>
        </div>

        {loading && !dados && (
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-24 rounded-2xl" />
            <Skeleton className="h-24 rounded-2xl" />
          </div>
        )}
        {dados && (
          <>
            <div className="grid grid-cols-2 gap-4">
              <KpiCard label="Total de Trocas" valor={formatCurrency(dados.total_trocas)} destaque />
              <KpiCard label="Taxa de Troca" valor={`${dados.taxa_troca_pct.toFixed(2)}%`} destaque />
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">
                Por produto <span className="text-gray-400 dark:text-gray-500 font-normal text-sm">({dados.por_produto.length})</span>
              </h2>
              {dados.por_produto.length === 0 ? (
                <p className="text-sm text-gray-400 dark:text-gray-500">Nenhuma troca no período.</p>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b dark:border-gray-700 text-left">
                      <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium">Código</th>
                      <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium">Produto</th>
                      <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium text-right">Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.por_produto.map((item, i) => (
                      <tr key={i} className="border-b dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="py-2 text-gray-400 dark:text-gray-500 font-mono">{item.codigo}</td>
                        <td className="py-2 text-gray-700 dark:text-gray-300">{item.produto}</td>
                        <td className="py-2 text-right font-semibold text-gray-800 dark:text-gray-100">{formatCurrency(item.receita)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
