import { useState, useCallback, useEffect, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { subDays, format } from 'date-fns'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import BiPageLayout from '../../components/bi/BiPageLayout'
import ExportButtons from '../../components/bi/ExportButtons'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import Card from '../../components/ui/Card'
import SectionHeader from '../../components/ui/SectionHeader'
import { fetchCurvaAbc, exportarExcelBI } from '../../api/bi'
import { baixarCSVdeArray } from '../../utils/csv'
import type { ItemCurvaAbcDTO, PeriodoBi, Dimensao, CurvaAbc } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { CURVA_CORES } from '../../utils/colors'
import { useBiCache } from '../../stores/biCache'
import { useToast } from '../../hooks/useToast'
import { PieChart as PieChartIcon } from 'lucide-react'
import Skeleton from '../../components/ui/Skeleton'
import DataTable from '../../components/ui/DataTable'
import type { Column } from '../../components/ui/DataTable'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const PRESETS_CURVA: Preset[] = [
  { label: '30 dias', kind: 'days', days: 30 },
  { label: '60 dias', kind: 'days', days: 60 },
  { label: '3 meses', kind: 'days', days: 90 },
  { label: 'Este mês', kind: 'current_month' },
]

function periodoInicial(): PeriodoBi {
  return {
    data_inicio: format(subDays(new Date(), 90), 'yyyy-MM-dd'),
    data_fim: format(new Date(), 'yyyy-MM-dd'),
  }
}

const CURVA_BADGE: Record<CurvaAbc, string> = {
  A: 'bg-abc-a-light text-abc-a',
  B: 'bg-abc-b-light text-abc-b',
  C: 'bg-abc-c-light text-abc-c',
}

export default function CurvaAbc() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [dimensao, setDimensao] = useState<Dimensao>(
    (searchParams.get('dimensao') as Dimensao) ?? 'produto'
  )
  const [dados, setDados] = useState<ItemCurvaAbcDTO[]>([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const navigate = useNavigate()
  const cache = useBiCache()
  const { toast } = useToast()

  const cacheKey = `curva-abc_${dimensao}`

  const buscar = useCallback(async (periodoOverride?: PeriodoBi, force = false) => {
    const p = periodoOverride ?? periodo
    if (!force) {
      const cached = cache.get<ItemCurvaAbcDTO[]>(cacheKey, p)
      if (cached) { setDados(cached); return }
    }
    setErro(null)
    setLoading(true)
    try {
      const data = await fetchCurvaAbc(p, dimensao)
      setDados(data)
      cache.set(cacheKey, p, data)
    } catch (e: unknown) {
      const err = e as { response?: { status?: number; data?: { detail?: string } } }
      if (err.response?.status === 400) setErro(err.response.data?.detail ?? 'Erro ao carregar dados.')
      else setErro('Erro ao carregar dados.')
    } finally {
      setLoading(false)
    }
  }, [periodo, dimensao, cache]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { const t = setTimeout(() => buscar()); return () => clearTimeout(t) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function syncParams(d: Dimensao) {
    const next = new URLSearchParams()
    if (d !== 'produto') next.set('dimensao', d)
    setSearchParams(next, { replace: true })
  }

  function handleBuscar(periodoOverride?: PeriodoBi) {
    cache.invalidate(cacheKey)
    buscar(periodoOverride, true)
  }

  const statsPorCurva = useMemo(() => {
    const totalReceita = dados.reduce((s, d) => s + d.receita, 0)
    const curvas = { A: { qtd: 0, receita: 0 }, B: { qtd: 0, receita: 0 }, C: { qtd: 0, receita: 0 } } as Record<CurvaAbc, { qtd: number; receita: number }>
    dados.forEach((d) => {
      curvas[d.curva].qtd++
      curvas[d.curva].receita += d.receita
    })
    return (Object.entries(curvas) as [CurvaAbc, { qtd: number; receita: number }][]).map(([curva, info]) => ({
      curva,
      ...info,
      pctReceita: totalReceita > 0 ? (info.receita / totalReceita) * 100 : 0,
    }))
  }, [dados])

  const pieData = statsPorCurva.map((s) => ({
    name: `Curva ${s.curva}`,
    value: s.receita,
  }))

  function buildColumns(): Column<ItemCurvaAbcDTO>[] {
    const cols: Column<ItemCurvaAbcDTO>[] = [
      { key: 'grupo', label: 'Grupo', width: '20%', render: (item) => <span className="truncate block" title={item.grupo}>{item.grupo}</span> },
    ]
    if (dimensao !== 'grupo') {
      cols.push({
        key: 'familia', label: 'Família', width: '20%',
        render: (item) => <span className="truncate block text-text-muted" title={item.familia ?? ''}>{item.familia ?? '\u2014'}</span>,
      })
    }
    if (dimensao === 'produto') {
      cols.push({
        key: 'produto', label: 'Produto', width: '20%',
        render: (item) => <span className="truncate block" title={item.produto ?? ''}>{item.produto ?? '\u2014'}</span>,
      })
    }
    cols.push(
      { key: 'receita', label: 'Receita', sortable: true, align: 'right', width: '120px', mono: true, render: (item) => <span className="font-semibold">{formatCurrency(item.receita)}</span> },
      { key: 'participacao_pct', label: 'Part. %', sortable: true, align: 'right', width: '100px', mono: true, render: (item) => <span className="text-text-secondary">{item.participacao_pct.toFixed(2)}%</span> },
      { key: 'participacao_acumulada', label: 'Acum. %', sortable: true, align: 'right', width: '100px', mono: true, render: (item) => <span className="text-text-secondary">{item.participacao_acumulada.toFixed(2)}%</span> },
      {
        key: 'curva', label: 'Curva', align: 'center', width: '80px',
        render: (item) => (
          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${CURVA_BADGE[item.curva]}`}>
            {item.curva}
          </span>
        ),
      },
    )
    return cols
  }

  return (
    <BiPageLayout titulo="Curva ABC" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Curva ABC' }]}>
      <Card variant="bordered">
        <div className="flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={handleBuscar} loading={loading} presets={PRESETS_CURVA} />
          <div className="flex flex-col gap-1">
            <label className="text-xs text-text-muted">Dimensão</label>
            <select
              className="border border-border bg-bg-hover text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-40"
              value={dimensao}
              onChange={(e) => { const val = e.target.value as Dimensao; setDimensao(val); syncParams(val) }}
            >
              <option value="produto">Produto</option>
              <option value="familia">Família</option>
              <option value="grupo">Grupo</option>
            </select>
          </div>
          {erro && <ErrorBanner message={erro} />}
          <ExportButtons
            onExcel={() => { exportarExcelBI(periodo, 'curva-abc', { dimensao }); toast({ type: 'success', message: 'Excel exportado' }) }}
            onCsv={() => { baixarCSVdeArray(dados, 'curva-abc'); toast({ type: 'success', message: 'CSV exportado' }) }}
            disabled={dados.length === 0}
          />
        </div>
      </Card>

      {loading && !dados.length && (
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} variant="kpi" />
          ))}
        </div>
      )}
      {!loading && dados.length === 0 && (
        <EmptyState title="Nenhum dado no período" description="Tente ampliar o período ou alterar os filtros." />
      )}
      {dados.length > 0 && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {statsPorCurva.map(({ curva, qtd, receita, pctReceita }) => (
              <Card key={curva} variant="bordered" padding="sm" className="flex flex-col items-center text-center gap-1">
                <span className={`text-xs font-semibold px-2 py-1 rounded-full ${CURVA_BADGE[curva]}`}>
                  Curva {curva}
                </span>
                <p className="text-xl font-bold text-text-primary break-words">{qtd}</p>
                <p className="text-xs text-text-muted">itens</p>
                <p className="text-sm font-semibold text-text-primary mt-1">{formatCurrency(receita)}</p>
                <p className="text-xs text-text-muted">{pctReceita.toFixed(1)}% da receita</p>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card variant="bordered">
              <SectionHeader icon={PieChartIcon}>Distribuição da Receita</SectionHeader>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                    animationBegin={0}
                    animationDuration={600}
                  >
                    {pieData.map((_, idx) => (
                      <Cell key={idx} fill={CURVA_CORES[statsPorCurva[idx].curva]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatCurrency(Number(v))} cursor={{ fill: 'rgba(100,100,100,0.06)' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-4 mt-2">
                {statsPorCurva.map(({ curva, pctReceita }) => (
                  <div key={curva} className="flex items-center gap-1.5 text-xs text-text-muted">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CURVA_CORES[curva] }} />
                    {curva} · {pctReceita.toFixed(1)}%
                  </div>
                ))}
              </div>
            </Card>

            <Card variant="bordered">
              <h2 className="text-sm font-semibold text-text-primary mb-4">Concentração Acumulada</h2>
              <p className="text-3xl font-bold text-text-primary">
                {statsPorCurva[0]?.pctReceita.toFixed(1) ?? 0}%
              </p>
              <p className="text-sm text-text-secondary">
                da receita está em {statsPorCurva[0]?.qtd ?? 0} itens da Curva A
              </p>
              {/* Visual gauge */}
              <div className="mt-4 h-2 bg-bg-hover rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary to-primary-light rounded-full transition-all duration-700"
                  style={{ width: `${statsPorCurva[0]?.pctReceita ?? 0}%` }}
                />
              </div>
              <div className="mt-3 flex flex-col gap-1 text-sm text-text-secondary">
                <p>· Curva A: {statsPorCurva[0]?.qtd ?? 0} itens · {statsPorCurva[0]?.pctReceita.toFixed(1) ?? 0}% receita</p>
                <p>· Curva B: {statsPorCurva[1]?.qtd ?? 0} itens · {statsPorCurva[1]?.pctReceita.toFixed(1) ?? 0}% receita</p>
                <p>· Curva C: {statsPorCurva[2]?.qtd ?? 0} itens · {statsPorCurva[2]?.pctReceita.toFixed(1) ?? 0}% receita</p>
              </div>
            </Card>
          </div>

          <Card variant="bordered">
            <SectionHeader>
              Classificação completa <span className="text-text-muted font-normal">({dados.length})</span>
            </SectionHeader>
            <DataTable
              data={dados}
              columns={buildColumns()}
              rowKey={(item) => `${item.grupo}-${item.familia ?? ''}-${item.produto ?? ''}`}
              onRowClick={(item) => item.codigo && navigate(`/bi/sku?codigo=${item.codigo}`)}
              density="sm"
              stickyHeader
              rowNumbers
            />
          </Card>
        </>
      )}
    </BiPageLayout>
  )
}
