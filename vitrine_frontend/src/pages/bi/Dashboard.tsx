import { useState, useCallback, useEffect } from 'react'
import { format } from 'date-fns'
import AdminHeader from '../../components/AdminHeader'
import BiSubNav from '../../components/bi/BiSubNav'
import PeriodoForm from '../../components/bi/PeriodoForm'
import KpiCard from '../../components/bi/KpiCard'
import { fetchKpis, fetchKpisComparativo, fetchRanking, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { KpisDTO, KpisComparativoDTO, ItemRankingDTO, PeriodoBi } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { useCountUp } from '../../hooks/useCountUp'
import Skeleton from '../../components/ui/Skeleton'

function periodoInicial(): PeriodoBi {
  const hoje = format(new Date(), 'yyyy-MM-dd')
  return { data_inicio: hoje, data_fim: hoje }
}

function variacaoInfo(pct: number | null): { valor: number; direcao: 'positivo' | 'negativo' | 'estavel' } | null {
  if (pct === null) return null
  if (pct > 0) return { valor: pct, direcao: 'positivo' }
  if (pct < 0) return { valor: pct, direcao: 'negativo' }
  return { valor: 0, direcao: 'estavel' }
}

export default function Dashboard() {
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [comparar, setComparar] = useState(true)
  const [kpis, setKpis] = useState<KpisDTO | null>(null)
  const [kpisComp, setKpisComp] = useState<KpisComparativoDTO | null>(null)
  const [topProdutos, setTopProdutos] = useState<ItemRankingDTO[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState('')
  const [pulseKey, setPulseKey] = useState(0)

  const kpisAtivos = kpisComp ?? kpis

  const animFatBruto = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.faturamento_bruto.atual : (kpis as KpisDTO).faturamento_bruto) : 0, 600, !!kpisAtivos)
  const animFatLiq = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.faturamento_liquido.atual : (kpis as KpisDTO).faturamento_liquido) : 0, 600, !!kpisAtivos)
  const animTrocas = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.total_trocas.atual : (kpis as KpisDTO).total_trocas) : 0, 600, !!kpisAtivos)
  const animTicketMedio = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.ticket_medio.atual : (kpis as KpisDTO).ticket_medio) : 0, 600, !!kpisAtivos)
  const animTickets = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.qtd_tickets.atual : (kpis as KpisDTO).qtd_tickets) : 0, 600, !!kpisAtivos)
  const animItensTicket = useCountUp(kpisAtivos ? (kpisComp ? kpisComp.itens_por_ticket.atual : (kpis as KpisDTO).itens_por_ticket) : 0, 600, !!kpisAtivos)
  const cache = useBiCache()
  const { toast } = useToast()

  const buscar = useCallback(async (force = false) => {
    if (!force) {
      const cached = cache.get<{ kpis: KpisDTO | KpisComparativoDTO; ranking: ItemRankingDTO[] }>('dashboard', periodo)
      if (cached) {
        if (comparar && 'faturamento_bruto' in cached.kpis && 'atual' in (cached.kpis as KpisComparativoDTO).faturamento_bruto) {
          setKpisComp(cached.kpis as KpisComparativoDTO)
          setKpis(null)
        } else if (!comparar && 'faturamento_bruto' in cached.kpis && !('atual' in (cached.kpis as KpisComparativoDTO).faturamento_bruto)) {
          setKpis(cached.kpis as KpisDTO)
          setKpisComp(null)
        } else {
          cache.clear()
        }
        setTopProdutos(cached.ranking)
        setPulseKey((prev) => prev + 1)
        return
      }
    }
    setErro('')
    setLoading(true)
    try {
      const kpisPromise = comparar ? fetchKpisComparativo(periodo) : fetchKpis(periodo)
      const rankingPromise = fetchRanking(periodo, 'receita_produto', 5)
      const [kpisData, rankingData] = await Promise.all([kpisPromise, rankingPromise])
      if (comparar) {
        setKpisComp(kpisData as KpisComparativoDTO)
        setKpis(null)
      } else {
        setKpis(kpisData as KpisDTO)
        setKpisComp(null)
      }
      setTopProdutos(rankingData)
      cache.set('dashboard', periodo, { kpis: kpisData, ranking: rankingData })
      setPulseKey((prev) => prev + 1)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados. Verifique a conexão com o servidor.')
    } finally {
      setLoading(false)
    }
  }, [periodo, comparar, cache])

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps -- Mount-only fetch via setTimeout; deps intentionally omitted -- Mount-only fetch via setTimeout; deps intentionally omitted

  function handleBuscar() {
    cache.clear()
    buscar(true)
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
      <AdminHeader titulo="BI" paginaAtual="bi" hideNav breadcrumb={[{ label: 'BI' }]} />
      <BiSubNav />

      <div className="w-full max-w-5xl flex flex-col gap-5">

        {/* Seletor de período */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
          <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Período de análise</h2>
          <PeriodoForm
            value={periodo}
            onChange={setPeriodo}
            onBuscar={handleBuscar}
            loading={loading}
          />
          <div className="flex items-center gap-2 mt-3">
            <label className="flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={comparar}
                onChange={(e) => setComparar(e.target.checked)}
                className="accent-primary w-4 h-4"
              />
              Comparar com ano anterior
            </label>
            {kpisComp?.dados_parciais_ate && (
              <span className="text-xs text-amber-600 bg-amber-50 dark:bg-amber-900/30 dark:text-amber-400 px-2 py-0.5 rounded-full ml-auto">
                ⏳ Dados parciais — atualizados até {kpisComp.dados_parciais_ate}
              </span>
            )}
          </div>
          {erro && <p className="text-red-500 text-sm mt-3">{erro}</p>}
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => { exportarExcelBI(periodo, 'kpis'); toast({ type: 'success', message: 'Excel exportado' }) }}
              disabled={!kpisAtivos}
              className="text-xs bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
            >
              Excel
            </button>
            <button
              onClick={() => { if (kpisAtivos) { baixarCSVdeArray([kpisAtivos], 'kpis'); toast({ type: 'success', message: 'CSV exportado' }) } }}
              disabled={!kpisAtivos}
              className="text-xs bg-gray-600 hover:bg-gray-700 disabled:opacity-40 text-white font-semibold px-3 py-1.5 rounded-lg transition"
            >
              CSV
            </button>
          </div>
        </div>

        {/* KPIs */}
        {loading && !kpisAtivos && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-2xl" />
            ))}
          </div>
        )}
        {kpisAtivos && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <KpiCard label="Faturamento Bruto" valor={formatCurrency(animFatBruto)} destaque delay={0} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.faturamento_bruto.variacao_pct) : null} />
            <KpiCard label="Faturamento Líquido" valor={formatCurrency(animFatLiq)} destaque delay={80} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.faturamento_liquido.variacao_pct) : null} />
            <KpiCard label="Total de Trocas" valor={formatCurrency(animTrocas)} delay={160} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.total_trocas.variacao_pct) : null} />
            <KpiCard label="Tickets" valor={Math.round(animTickets).toLocaleString('pt-BR')} delay={240} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.qtd_tickets.variacao_pct) : null} />
            <KpiCard label="Ticket Médio" valor={formatCurrency(animTicketMedio)} delay={320} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.ticket_medio.variacao_pct) : null} />
            <KpiCard label="Itens por Ticket" valor={animItensTicket.toFixed(2)} delay={400} pulseKey={pulseKey}
              variacao={kpisComp ? variacaoInfo(kpisComp.itens_por_ticket.variacao_pct) : null} />
          </div>
        )}

        {/* Top 5 produtos */}
        {loading && !topProdutos.length && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
            <Skeleton className="h-5 w-48 mb-4" />
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-6 w-full mb-2" />
            ))}
          </div>
        )}
        {topProdutos.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5">
            <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200 mb-4">Top 5 Produtos mais vendidos</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b dark:border-gray-700 text-left">
                  <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium w-8">#</th>
                  <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium">Produto</th>
                  <th className="pb-2 text-xs text-gray-400 dark:text-gray-500 font-medium text-right">Valor</th>
                </tr>
              </thead>
              <tbody>
                {topProdutos.map((item, i) => (
                  <tr key={item.codigo} className="border-b dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="py-2 text-gray-400 dark:text-gray-500 font-semibold">{i + 1}</td>
                    <td className="py-2 text-gray-700 dark:text-gray-300">
                      <span className="text-gray-400 dark:text-gray-500 font-mono mr-1">{item.codigo}</span>
                      {item.produto}
                    </td>
                    <td className="py-2 text-right font-semibold text-gray-800 dark:text-gray-100">{formatCurrency(item.valor)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </div>
  )
}