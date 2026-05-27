import { useState, useCallback, useEffect, useRef } from 'react'
import { format } from 'date-fns'
import {
  fetchKpis, fetchKpisComparativo, fetchRanking, fetchDiario,
  fetchDiarioComparativo, fetchTemporalHora, fetchCurvaAbc,
  exportarExcelBI, exportarPDF,
} from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import { getConfigsCache } from '../../stores/configStore'
import { formatCurrency } from '../../utils/formatters'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { useCountUp } from '../../hooks/useCountUp'
import BiPageLayout from '../../components/bi/BiPageLayout'
import DashboardTopBar from '../../components/bi/DashboardTopBar'
import DashboardHero from '../../components/bi/DashboardHero'
import DashboardSecondaryKpis from '../../components/bi/DashboardSecondaryKpis'
import DashboardCharts from '../../components/bi/DashboardCharts'
import ResumoDia from '../../components/bi/ResumoDia'
import CurvaAbcPreview from '../../components/bi/CurvaAbcPreview'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import type {
  KpisDTO, KpisComparativoDTO, ItemRankingDTO,
  PontoDiarioDTO, PontoHoraDTO, DiarioComparativoDTO,
  PeriodoBi, ItemCurvaAbcDTO,
} from '../../types'
import { variacaoInfo } from './dashboardHelpers'

// Default period: current month
function periodoInicial(): PeriodoBi {
  const hoje = new Date()
  return {
    data_inicio: format(hoje, 'yyyy-MM-01'),
    data_fim: format(hoje, 'yyyy-MM-dd'),
  }
}

function periodoMesAtual(): PeriodoBi {
  const hoje = new Date()
  return {
    data_inicio: format(hoje, 'yyyy-MM-01'),
    data_fim: format(hoje, 'yyyy-MM-dd'),
  }
}

type KpiKeys = 'faturamento_bruto' | 'faturamento_liquido' | 'total_trocas' | 'qtd_tickets' | 'ticket_medio' | 'itens_por_ticket'

export default function Dashboard() {
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [comparar, setComparar] = useState(true)
  const [kpis, setKpis] = useState<KpisDTO | null>(null)
  const [kpisComp, setKpisComp] = useState<KpisComparativoDTO | null>(null)
  const [topProdutos, setTopProdutos] = useState<ItemRankingDTO[]>([])
  const [curvaAbc, setCurvaAbc] = useState<ItemCurvaAbcDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [pulseKey, setPulseKey] = useState(0)

  // ── Meta / Projeção ──
  const [metaMensal, setMetaMensal] = useState<number | null>(null)
  const [receitaMesAtual, setReceitaMesAtual] = useState<number | null>(null)
  const [loadingMeta, setLoadingMeta] = useState(true)

  // ── Gráficos de tendência ──
  const [diarioReceita, setDiarioReceita] = useState<PontoDiarioDTO[]>([])
  const [diarioTicketMedio, setDiarioTicketMedio] = useState<PontoDiarioDTO[]>([])
  const [diarioTickets, setDiarioTickets] = useState<PontoDiarioDTO[]>([])
  const [loadingDiario, setLoadingDiario] = useState(true)

  // ── Gráfico de receita por hora ──
  const [dadosHora, setDadosHora] = useState<PontoHoraDTO[]>([])
  const [loadingHora, setLoadingHora] = useState(true)

  // ── Comparativo do último dia (backed by /diario/comparativo) ──
  const [diarioComparativo, setDiarioComparativo] = useState<{
    receita: DiarioComparativoDTO | null
    tickets: DiarioComparativoDTO | null
    ticketMedio: DiarioComparativoDTO | null
  }>({ receita: null, tickets: null, ticketMedio: null })

  // Determina qual fonte de dados usar (comparativo ou simples)
  const kpisAtivos = kpisComp ?? kpis
  const temComparativo = !!kpisComp

  // Animações countUp
  const animFatBrutoOrig = (() => {
    if (!kpisAtivos) return 0
    if (temComparativo) return (kpisAtivos as KpisComparativoDTO).faturamento_bruto.atual
    return (kpisAtivos as KpisDTO).faturamento_bruto
  })()
  const animFatBruto = useCountUp(animFatBrutoOrig, 600, !!kpisAtivos)

  const getKpi = useCallback((key: KpiKeys): number => {
    if (!kpisAtivos) return 0
    if (temComparativo) {
      const comp = kpisAtivos as KpisComparativoDTO
      return comp[key]?.atual ?? 0
    }
    return (kpisAtivos as KpisDTO)[key] ?? 0
  }, [kpisAtivos, temComparativo])

  const getVariacao = useCallback((key: KpiKeys): number | null => {
    if (!temComparativo) return null
    const comp = kpisAtivos as KpisComparativoDTO
    return comp[key]?.variacao_pct ?? null
  }, [kpisAtivos, temComparativo])

  const getAnterior = useCallback((key: KpiKeys): number | null => {
    if (!temComparativo) return null
    const comp = kpisAtivos as KpisComparativoDTO
    return comp[key]?.anterior ?? null
  }, [kpisAtivos, temComparativo])

  const animFatLiq = useCountUp(getKpi('faturamento_liquido'), 600, !!kpisAtivos)
  const animItensTicket = useCountUp(getKpi('itens_por_ticket'), 600, !!kpisAtivos)
  const animTicketMedio = useCountUp(getKpi('ticket_medio'), 600, !!kpisAtivos)
  const animTickets = useCountUp(getKpi('qtd_tickets'), 600, !!kpisAtivos)

  const cache = useBiCache()
  const cacheKey = `dashboard_${comparar}`
  const cacheTimestamp = cache.getTimestamp(cacheKey, periodo)
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 30000); return () => clearInterval(t) }, [])
  const cacheFresh = cacheTimestamp ? cacheTimestamp > now - 300000 : false
  const { toast } = useToast()

  // ── Carregar meta + receita do mês atual ──
  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal
    getConfigsCache().then((c) => {
      const val = c.meta_faturamento_mensal
      if (val && Number(val) > 0) setMetaMensal(Number(val))
    }).catch(() => {})
    fetchKpis(periodoMesAtual(), signal)
      .then((k) => setReceitaMesAtual(k.faturamento_bruto))
      .catch(err => {
        if (err?.name !== 'CanceledError' && err?.name !== 'AbortError') {
          // silent
        }
      })
      .finally(() => setLoadingMeta(false))
    return () => controller.abort()
  }, [])

  // ── Carregar dados diários + comparativo ──
  const buscarDiario = useCallback(async (p: PeriodoBi, signal?: AbortSignal) => {
    if (p.data_inicio === p.data_fim) {
      setDiarioReceita([])
      setDiarioTicketMedio([])
      setDiarioTickets([])
      setDadosHora([])
      setDiarioComparativo({ receita: null, tickets: null, ticketMedio: null })
      setLoadingDiario(false)
      setLoadingHora(false)
      return
    }
    setLoadingDiario(true)
    setLoadingHora(true)
    try {
      const [rc, tm, qt, hora] = await Promise.all([
        fetchDiario(p, 'receita_produto', signal),
        fetchDiario(p, 'ticket_medio', signal),
        fetchDiario(p, 'qtd_tickets', signal),
        fetchTemporalHora(p, 'receita_produto', signal),
      ])
      setDiarioReceita(rc)
      setDiarioTicketMedio(tm)
      setDiarioTickets(qt)
      setDadosHora(hora)

      if (comparar) {
        try {
          const [compRc, compTk, compTm] = await Promise.all([
            fetchDiarioComparativo(p, 'receita_produto', signal),
            fetchDiarioComparativo(p, 'qtd_tickets', signal),
            fetchDiarioComparativo(p, 'ticket_medio', signal),
          ])
          setDiarioComparativo({ receita: compRc, tickets: compTk, ticketMedio: compTm })
        } catch {
          setDiarioComparativo({ receita: null, tickets: null, ticketMedio: null })
        }
      } else {
        setDiarioComparativo({ receita: null, tickets: null, ticketMedio: null })
      }
    } catch {
      // silencioso — série diária falhou
    } finally {
      setLoadingDiario(false)
      setLoadingHora(false)
    }
  }, [comparar])

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false, signal?: AbortSignal) => {
    const p = periodoOverride ?? periodo
    buscarDiario(p, signal)
    if (!force) {
      const cached = cache.get<{ kpis: KpisDTO | KpisComparativoDTO; ranking: ItemRankingDTO[] }>(cacheKey, p)
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
    setErro(null)
    setLoading(true)
    try {
      const kpisPromise = comparar ? fetchKpisComparativo(p, signal) : fetchKpis(p, signal)
      const rankingPromise = fetchRanking(p, 'receita_produto', 5, signal)
      const [kpisData, rankingData] = await Promise.all([kpisPromise, rankingPromise])
      if (comparar) {
        setKpisComp(kpisData as KpisComparativoDTO)
        setKpis(null)
      } else {
        setKpis(kpisData as KpisDTO)
        setKpisComp(null)
      }
      setTopProdutos(rankingData)
      cache.set(cacheKey, p, { kpis: kpisData, ranking: rankingData })
      setPulseKey((prev) => prev + 1)

      // Busca Curva ABC (best-effort, não bloqueia o cache principal)
      try {
        const abc = await fetchCurvaAbc(p, 'produto', signal)
        setCurvaAbc(abc)
      } catch {
        // silencioso
      }
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } }; name?: string }
      if (err?.name === 'CanceledError' || err?.name === 'AbortError') return
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados. Verifique a conexão com o servidor.')
    } finally {
      setLoading(false)
    }
  }, [periodo, comparar, cache, cacheKey, buscarDiario])

  const isFirstRender = useRef(true)
  useEffect(() => {
    const controller = new AbortController()
    const signal = controller.signal
    if (isFirstRender.current) {
      isFirstRender.current = false
      buscar(undefined, undefined, signal)
    } else {
      cache.invalidate(cacheKey)
      buscar(undefined, true, signal)
    }
    return () => controller.abort()
  }, [comparar]) // eslint-disable-line react-hooks/exhaustive-deps

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.invalidate(cacheKey)
    buscar(periodoOverride, true)
  }

  // ── Cálculos de meta / projeção ──
  const hoje = new Date()
  const diasCorridos = hoje.getDate()
  const ultimoDiaMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0).getDate()
  const pctMeta = metaMensal && receitaMesAtual ? (receitaMesAtual / metaMensal) * 100 : null
  const projecao = receitaMesAtual != null && diasCorridos > 0
    ? (receitaMesAtual / diasCorridos) * ultimoDiaMes
    : null
  const projecaoVsMeta = metaMensal && projecao ? ((projecao / metaMensal) * 100) - 100 : null

  // ── Dados para SecondaryKPIs ──
  const secondaryKpiItems = [
    {
      label: 'Faturamento Líquido',
      valor: formatCurrency(animFatLiq),
      delay: 80,
      variacao: temComparativo ? variacaoInfo(getVariacao('faturamento_liquido')) : null,
      valorAnterior: getAnterior('faturamento_liquido') != null ? formatCurrency(getAnterior('faturamento_liquido')!) : undefined,
    },
    {
      label: 'Itens por Ticket',
      valor: animItensTicket.toFixed(2),
      delay: 160,
      variacao: temComparativo ? variacaoInfo(getVariacao('itens_por_ticket')) : null,
      valorAnterior: getAnterior('itens_por_ticket') != null ? getAnterior('itens_por_ticket')!.toFixed(2) : undefined,
    },
    {
      label: 'Tickets',
      valor: Math.round(animTickets).toLocaleString('pt-BR'),
      delay: 240,
      variacao: temComparativo ? variacaoInfo(getVariacao('qtd_tickets')) : null,
      valorAnterior: getAnterior('qtd_tickets') != null ? Math.round(getAnterior('qtd_tickets')!).toLocaleString('pt-BR') : undefined,
    },
    {
      label: 'Ticket Médio',
      valor: formatCurrency(animTicketMedio),
      delay: 320,
      variacao: temComparativo ? variacaoInfo(getVariacao('ticket_medio')) : null,
      valorAnterior: getAnterior('ticket_medio') != null ? formatCurrency(getAnterior('ticket_medio')!) : undefined,
    },
  ]

  return (
    <BiPageLayout titulo="Dashboard" breadcrumb={[{ label: 'BI' }, { label: 'Dashboard' }]}>
      {/* ── Top Bar ── */}
      <DashboardTopBar
        periodo={periodo}
        setPeriodo={setPeriodo}
        loading={loading}
        comparar={comparar}
        onToggleComparar={() => setComparar((prev) => !prev)}
        onBuscar={handleBuscar}
        disabled={!kpisAtivos}
        cacheTimestamp={cacheTimestamp}
        cacheFresh={cacheFresh}
        dadosParciaisAte={kpisComp?.dados_parciais_ate ?? null}
        onExcel={() => { exportarExcelBI(periodo, 'kpis'); toast({ type: 'success', message: 'Excel exportado' }) }}
        onPdf={async () => {
          const ok = await exportarPDF()
          if (ok) {
            toast({ type: 'success', message: 'PDF exportado' })
          } else {
            toast({ type: 'info', message: 'Usando impressão do navegador...' })
            window.print()
          }
        }}
        onCsv={() => { if (kpisAtivos) { baixarCSVdeArray([kpisAtivos], 'kpis'); toast({ type: 'success', message: 'CSV exportado' }) } }}
      />

      {erro && <ErrorBanner message={erro} />}

      {/* ── Hero + Top Produtos ── */}
      <DashboardHero
        fatBruto={formatCurrency(animFatBruto)}
        pulseKey={pulseKey}
        fatBrutoVariacao={temComparativo ? variacaoInfo(getVariacao('faturamento_bruto')) : null}
        fatBrutoAnterior={getAnterior('faturamento_bruto') != null ? formatCurrency(getAnterior('faturamento_bruto')!) : undefined}
        pctMeta={pctMeta}
        loadingMeta={loadingMeta}
        receitaMesAtual={receitaMesAtual ?? 0}
        metaMensal={metaMensal ?? 0}
        projecao={projecao}
        projecaoVsMeta={projecaoVsMeta}
        diasCorridos={diasCorridos}
        ultimoDiaMes={ultimoDiaMes}
        topProdutos={topProdutos}
        loading={loading}
        kpisAtivos={!!kpisAtivos}
      />

      {/* ── Empty state ── */}
      {!kpisAtivos && !loading && !erro && (
        <EmptyState title="Selecione um período" description="Escolha um período para analisar os dados." />
      )}

      {/* ── Resumo do Dia ── */}
      {kpisAtivos && diarioReceita.length > 0 && (
        <ResumoDia
          receita={diarioReceita}
          tickets={diarioTickets}
          ticketMedio={diarioTicketMedio}
          comparar={comparar}
          comparativo={diarioComparativo}
        />
      )}

      {/* ── Resumo do Dia skeleton ── */}
      {kpisAtivos && loadingDiario && diarioReceita.length === 0 && (
        <div className="bg-bg-card border border-border rounded-xl p-4">
          <div className="grid grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-2">
                <div className="h-3 w-16 bg-bg-hover rounded animate-pulse" />
                <div className="h-6 w-24 bg-bg-hover rounded animate-pulse" />
                <div className="h-3 w-20 bg-bg-hover rounded animate-pulse" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Secondary KPIs (4 cards) ── */}
      <DashboardSecondaryKpis
        items={secondaryKpiItems}
        visible={!!kpisAtivos}
        loading={loading && !kpisAtivos && !erro}
      />

      {/* ── Charts: Tendências + Receita por Hora ── */}
      <DashboardCharts
        diarioTicketMedio={diarioTicketMedio}
        diarioTickets={diarioTickets}
        dadosHora={dadosHora}
        loadingDiario={loadingDiario}
        loadingHora={loadingHora}
      />

      {/* ── Curva ABC ── */}
      {(curvaAbc.length > 0 || loading) && (
        <CurvaAbcPreview data={curvaAbc} loading={loading} />
      )}
    </BiPageLayout>
  )
}
