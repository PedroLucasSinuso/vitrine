import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { subDays, format } from 'date-fns'
import PeriodoForm from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import Card from '../../components/ui/Card'
import SectionHeader from '../../components/ui/SectionHeader'
import ProgressBar from '../../components/ui/ProgressBar'
import KpiCard from '../../components/bi/KpiCard'
import { fetchPerdas, fetchConsumo, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { MovimentoDTO, PeriodoBi } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { useCountUp } from '../../hooks/useCountUp'
import { TrendingDown, PackageOpen } from 'lucide-react'
import Skeleton from '../../components/ui/Skeleton'

function periodoInicial(): PeriodoBi {
  return {
    data_inicio: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    data_fim: format(new Date(), 'yyyy-MM-dd'),
  }
}

type Aba = 'perdas' | 'consumo'

function TabelaMovimento({ dados }: { dados: MovimentoDTO }) {
  const navigate = useNavigate()
  const maximo = dados.por_produto[0]?.receita ?? 1
  const animTotal = useCountUp(dados.total, 600, true)
  return (
    <>
      <KpiCard label="Total" valor={formatCurrency(animTotal)} />
      <Card variant="bordered">
        <SectionHeader>
          Por produto <span className="text-slate-400 dark:text-slate-500 font-normal">({dados.por_produto.length})</span>
        </SectionHeader>
        {dados.por_produto.length === 0 ? (
          <p className="text-sm text-slate-400 dark:text-slate-500">Nenhum registro no período.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {dados.por_produto.slice(0, 20).map((item, i) => (
              <div
                key={i}
                onClick={() => navigate(`/bi/sku?codigo=${item.codigo}`)}
                className="flex flex-col gap-0.5 cursor-pointer"
              >
                <div className="flex justify-between text-sm">
                  <span className="text-slate-700 dark:text-slate-300 truncate">
                    <span className="text-slate-400 dark:text-slate-500 font-mono mr-1">{item.codigo}</span>
                    {item.produto}
                  </span>
                  <span className="font-semibold text-slate-800 dark:text-slate-100 shrink-0 ml-2">{formatCurrency(item.receita)}</span>
                </div>
                <ProgressBar value={item.receita} max={maximo} />
              </div>
            ))}
            {dados.por_produto.length > 20 && (
              <p className="text-xs text-slate-400 dark:text-slate-500 text-center">
                +{dados.por_produto.length - 20} produtos não listados
              </p>
            )}
          </div>
        )}
      </Card>
    </>
  )
}

export default function PerdasConsumo() {
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [aba, setAba] = useState<Aba>('perdas')
  const [perdas, setPerdas] = useState<MovimentoDTO | null>(null)
  const [consumo, setConsumo] = useState<MovimentoDTO | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const cache = useBiCache()
  const { toast } = useToast()

  const buscar = useCallback(async (force = false) => {
    if (!force) {
      const cacheKeyP = `perdas_${periodo.data_inicio}_${periodo.data_fim}`
      const cacheKeyC = `consumo_${periodo.data_inicio}_${periodo.data_fim}`
      const cachedP = cache.get<MovimentoDTO>(cacheKeyP, periodo)
      const cachedC = cache.get<MovimentoDTO>(cacheKeyC, periodo)
      if (cachedP && cachedC) { setPerdas(cachedP); setConsumo(cachedC); return }
    }
    setErro(null)
    setLoading(true)
    try {
      const [p, c] = await Promise.all([fetchPerdas(periodo), fetchConsumo(periodo)])
      setPerdas(p)
      setConsumo(c)
      cache.set(`perdas_${periodo.data_inicio}_${periodo.data_fim}`, periodo, p)
      cache.set(`consumo_${periodo.data_inicio}_${periodo.data_fim}`, periodo, c)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [periodo, cache])

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function handleBuscar() {
    cache.invalidate(`perdas_${periodo.data_inicio}_${periodo.data_fim}`)
    cache.invalidate(`consumo_${periodo.data_inicio}_${periodo.data_fim}`)
    buscar(true)
  }

  const dadosAtivos = aba === 'perdas' ? perdas : consumo
  const animPerdas = useCountUp(perdas?.total ?? 0, 600, !!perdas)
  const animConsumo = useCountUp(consumo?.total ?? 0, 600, !!consumo)

  return (
    <BiPageLayout titulo="Perdas e Consumo" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Perdas e Consumo' }]}>
      <Card variant="bordered">
        <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} />
        {erro && <div className="mt-3"><ErrorBanner message={erro} /></div>}
        <div className="mt-3">
          <ExportButtons
            onExcel={() => { exportarExcelBI(periodo, aba); toast({ type: 'success', message: 'Excel exportado' }) }}
            onCsv={() => { if (dadosAtivos) { baixarCSVdeArray(dadosAtivos.por_produto, aba); toast({ type: 'success', message: 'CSV exportado' }) } }}
            disabled={!dadosAtivos}
          />
        </div>
      </Card>

      {loading && !perdas && !consumo && (
        <div className="flex flex-col gap-4">
          <Skeleton variant="kpi" />
          <Skeleton variant="chart" />
        </div>
      )}
      {!loading && !perdas && !consumo && !erro && (
        <EmptyState title="Nenhum dado no período" description="Tente ampliar o período." />
      )}
      {(perdas || consumo) && (
        <>
          {perdas && consumo && (
            <div className="grid grid-cols-2 gap-3">
              <Card variant="bordered" className="flex flex-col items-center text-center gap-1 p-4">
                <TrendingDown size={16} className="text-red-500" />
                <p className="text-xs text-slate-400 dark:text-slate-500 font-medium">Perdas</p>
                <p className="text-xl font-bold text-red-600">{formatCurrency(animPerdas)}</p>
                <p className="text-xs text-slate-400 dark:text-slate-500">{perdas.por_produto.length} produtos</p>
              </Card>
              <Card variant="bordered" className="flex flex-col items-center text-center gap-1 p-4">
                <PackageOpen size={16} className="text-amber-500" />
                <p className="text-xs text-slate-400 dark:text-slate-500 font-medium">Consumo</p>
                <p className="text-xl font-bold text-amber-600">{formatCurrency(animConsumo)}</p>
                <p className="text-xs text-slate-400 dark:text-slate-500">{consumo.por_produto.length} produtos</p>
              </Card>
              <Card variant="bordered" className="flex flex-col items-center text-center gap-1 p-4 col-span-2">
                <p className="text-xs text-slate-400 dark:text-slate-500 font-medium">Proporção</p>
                <p className="text-xl font-bold text-slate-800 dark:text-slate-100">
                  {perdas.total > 0
                    ? `${((consumo.total / perdas.total) * 100).toFixed(1)}%`
                    : '\u2014'}
                </p>
                <p className="text-xs text-slate-400 dark:text-slate-500">consumo em relação a perdas</p>
              </Card>
            </div>
          )}

          <div className="flex gap-1 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-1 w-fit">
            {(['perdas', 'consumo'] as Aba[]).map((a) => (
              <button
                key={a}
                onClick={() => setAba(a)}
                className={`px-5 py-2 rounded-xl text-sm font-semibold transition capitalize ${
                  aba === a ? 'bg-primary text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                {a}
              </button>
            ))}
          </div>

          {dadosAtivos && <TabelaMovimento dados={dadosAtivos} />}
        </>
      )}
    </BiPageLayout>
  )
}
