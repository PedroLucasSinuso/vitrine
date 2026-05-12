import { useState, useCallback, useEffect } from 'react'
import { subDays, format } from 'date-fns'
import AdminHeader from '../../components/AdminHeader'
import BiSubNav from '../../components/bi/BiSubNav'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import { fetchCurvaAbc, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { ItemCurvaAbcDTO, PeriodoBi, Dimensao, CurvaAbc } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import Skeleton from '../../components/ui/Skeleton'

const PRESETS_CURVA: Preset[] = [
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

const CURVA_BADGE: Record<CurvaAbc, string> = {
  A: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  B: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  C: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300',
}

export default function CurvaAbc() {
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [dimensao, setDimensao] = useState<Dimensao>('produto')
  const [dados, setDados] = useState<ItemCurvaAbcDTO[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const cache = useBiCache()
  const { toast } = useToast()

  const buscar = useCallback(async (force = false) => {
    const cacheKey = `curva-abc_${dimensao}`
    if (!force) {
      const cached = cache.get<ItemCurvaAbcDTO[]>(cacheKey, periodo)
      if (cached) { setDados(cached); return }
    }
    setErro('')
    setLoading(true)
    try {
      const data = await fetchCurvaAbc(periodo, dimensao)
      setDados(data)
      cache.set(cacheKey, periodo, data)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [periodo, dimensao, cache])

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps -- Mount-only fetch via setTimeout; deps intentionally omitted -- Mount-only fetch via setTimeout; deps intentionally omitted

  function handleBuscar() {
    cache.clear()
    buscar(true)
  }

  const contagem = { A: 0, B: 0, C: 0 }
  dados.forEach((d) => contagem[d.curva]++)

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
      <AdminHeader titulo="Curva ABC" paginaAtual="bi" hideNav breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Curva ABC' }]} />
      <BiSubNav />

      <div className="w-full max-w-5xl flex flex-col gap-5">

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_CURVA} />
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400">Dimensão</label>
            <select
              className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-40"
              value={dimensao}
              onChange={(e) => setDimensao(e.target.value as Dimensao)}
            >
              <option value="produto">Produto</option>
              <option value="familia">Família</option>
              <option value="grupo">Grupo</option>
            </select>
          </div>
          {erro && <p className="text-red-500 text-sm">{erro}</p>}
          <div className="flex gap-2">
            <button
              onClick={() => { exportarExcelBI(periodo, 'curva-abc', { dimensao }); toast({ type: 'success', message: 'Excel exportado' }) }}
              disabled={dados.length === 0}
              className="text-xs bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
            >
              Excel
            </button>
            <button
              onClick={() => { baixarCSVdeArray(dados, 'curva-abc'); toast({ type: 'success', message: 'CSV exportado' }) }}
              disabled={dados.length === 0}
              className="text-xs bg-gray-600 hover:bg-gray-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
            >
              CSV
            </button>
          </div>
        </div>

        {loading && !dados.length && (
          <div className="grid grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-2xl" />
            ))}
          </div>
        )}
        {dados.length > 0 && (
          <>
            {/* Resumo por curva */}
            <div className="grid grid-cols-3 gap-4">
              {(['A', 'B', 'C'] as CurvaAbc[]).map((curva) => (
                <div key={curva} className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-4 flex flex-col gap-1">
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full w-fit ${CURVA_BADGE[curva]}`}>
                    Curva {curva}
                  </span>
                  <p className="text-xl font-bold text-gray-800 dark:text-gray-100 break-words">{contagem[curva]}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">itens</p>
                </div>
              ))}
            </div>

            {/* Tabela */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
              <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">
                Classificação completa <span className="text-gray-400 dark:text-gray-500 font-normal text-sm">({dados.length})</span>
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b dark:border-gray-700 text-left">
                      <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium">#</th>
                      <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium">Grupo</th>
                      {dimensao !== 'grupo' && <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium">Família</th>}
                      {dimensao === 'produto' && <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium">Produto</th>}
                      <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium text-right">Receita</th>
                      <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium text-right">Part. %</th>
                      <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium text-right">Acum. %</th>
                      <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium text-center">Curva</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.map((item, i) => (
                      <tr key={i} className="border-b dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="py-2 text-gray-400 dark:text-gray-500">{i + 1}</td>
                        <td className="py-2 text-gray-700 dark:text-gray-300">{item.grupo}</td>
                        {dimensao !== 'grupo' && <td className="py-2 text-gray-500 dark:text-gray-400">{item.familia ?? '—'}</td>}
                        {dimensao === 'produto' && <td className="py-2 text-gray-700 dark:text-gray-300">{item.produto ?? '—'}</td>}
                        <td className="py-2 text-right font-semibold text-gray-800 dark:text-gray-100">{formatCurrency(item.receita)}</td>
                        <td className="py-2 text-right text-gray-600 dark:text-gray-400">{item.participacao_pct.toFixed(2)}%</td>
                        <td className="py-2 text-right text-gray-600 dark:text-gray-400">{item.participacao_acumulada.toFixed(2)}%</td>
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
            </div>
          </>
        )}
      </div>
    </div>
  )
}
