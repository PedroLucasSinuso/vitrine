import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, startOfMonth } from 'date-fns'
import {
  Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { Info, TrendingUp, UserMinus, UserPlus, Users } from 'lucide-react'
import BiPageLayout from '../../components/bi/BiPageLayout'
import EvolucaoMensal from '../../components/bi/EvolucaoMensal'
import Button from '../../components/ui/Button'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import Card from '../../components/ui/Card'
import DataTable, { type Column } from '../../components/ui/DataTable'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import KpiCard from '../../components/ui/KpiCard'
import Modal from '../../components/ui/Modal'
import ProgressBar from '../../components/ui/ProgressBar'
import SectionHeader from '../../components/ui/SectionHeader'
import Skeleton from '../../components/ui/Skeleton'
import { fetchEquipe, fetchMixVendedor, fetchSerieMensal, fetchSerieVendedor } from '../../api/equipe'
import { listarDatasets } from '../../api/importacao'
import { CHART_THEME } from '../../config/chartTheme'
import { usePerfilEmpresa } from '../../stores/perfilEmpresaContexto'
import type {
  IndicadoresVendedor, ItemMixVendedor, PeriodoBi, PontoMensal, PontoSerieVendedor, ResultadoEquipe,
} from '../../types'
import { formatCurrency } from '../../utils/formatters'
import {
  comparadoALoja, direcaoVariacao, pontosDaEvolucao, textoDeComparacao, formatarDataCurta, formatarDecimal, formatarPercentual, formatarVariacao, periodosImportados, taxaDeTroca,
} from '../../utils/equipe'

const PRESETS: Preset[] = [
  { label: 'Este mês', kind: 'current_month' },
  { label: 'Mês passado', kind: 'last_month' },
  { label: '30 dias', kind: 'days', days: 30 },
]

function periodoInicial(): PeriodoBi {
  return {
    data_inicio: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
    data_fim: format(new Date(), 'yyyy-MM-dd'),
  }
}

function Variacao({ valor }: { valor: number | null }) {
  const direcao = direcaoVariacao(valor)
  const classe = direcao === 'positivo' ? 'text-success' : direcao === 'negativo' ? 'text-danger' : 'text-text-muted'
  const seta = direcao === 'positivo' ? '▲ ' : direcao === 'negativo' ? '▼ ' : ''
  return <span className={`text-xs font-medium ${classe}`}>{valor === null ? '—' : `${seta}${formatarVariacao(valor)}`}</span>
}

function TooltipParticipacao({ active, payload }: { active?: boolean; payload?: { payload: IndicadoresVendedor }[] }) {
  if (!active || !payload?.length) return null
  const item = payload[0].payload
  return (
    <div style={CHART_THEME.tooltip.contentStyle} className="px-3 py-2">
      <p className="font-semibold text-text-primary">{item.vendedor}</p>
      <p className="text-text-secondary">{formatCurrency(item.faturamento_bruto)} · {formatarPercentual(item.participacao)}</p>
    </div>
  )
}

function DetalheVendedor({
  vendedor, periodo, resultado, onClose,
}: { vendedor: IndicadoresVendedor; periodo: PeriodoBi; resultado: ResultadoEquipe; onClose: () => void }) {
  const { rotulo } = usePerfilEmpresa()
  const navigate = useNavigate()
  const [serie, setSerie] = useState<PontoSerieVendedor[] | null>(null)
  const [mix, setMix] = useState<ItemMixVendedor[] | null>(null)
  const indisponivel: Record<string, string> = Object.fromEntries(resultado.indisponivel.map((i) => [i.indicador, i.motivo]))
  const chave = vendedor.sem_vendedor ? null : vendedor.vendedor
  const semSerie = Boolean(indisponivel.serie_diaria)
  const semMix = Boolean(indisponivel.mix_categoria)

  useEffect(() => {
    if (!semSerie) fetchSerieVendedor(periodo, chave).then(setSerie).catch(() => setSerie([]))
    if (!semMix) fetchMixVendedor(periodo, chave).then(setMix).catch(() => setMix([]))
  }, [chave, periodo, semSerie, semMix])

  const loja = resultado.loja
  const comparacoes = [
    { rotulo: 'Ticket médio', valor: formatCurrency(vendedor.ticket_medio), vsLoja: comparadoALoja(vendedor.ticket_medio, loja.ticket_medio) },
    { rotulo: 'Peças por atendimento', valor: formatarDecimal(vendedor.pa), vsLoja: comparadoALoja(vendedor.pa, loja.pa) },
    { rotulo: 'Taxa de troca', valor: formatarPercentual(taxaDeTroca(vendedor)), vsLoja: null },
  ]

  return (
    <Modal
      open
      onClose={onClose}
      title={vendedor.vendedor}
      size="lg"
      actions={vendedor.sem_vendedor ? undefined : (
        <Button
          variant="outline"
          onClick={() => navigate(`/bi/equipe/vendedor?${new URLSearchParams({ nome: vendedor.vendedor, inicio: periodo.data_inicio, fim: periodo.data_fim })}`)}
        >
          Ver análise completa
        </Button>
      )}
    >
      <div className="flex flex-col gap-5">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {comparacoes.map((c) => (
            <div key={c.rotulo} className="rounded-lg border border-border p-3">
              <p className="text-xs text-text-muted">{c.rotulo}</p>
              <p className="text-lg font-semibold text-text-primary">{c.valor}</p>
              {c.vsLoja !== null && (
                <p className="text-xs text-text-muted">vs média da loja: <Variacao valor={c.vsLoja} /></p>
              )}
            </div>
          ))}
        </div>

        <section>
          <SectionHeader icon={TrendingUp}>Evolução diária</SectionHeader>
          {indisponivel.serie_diaria ? (
            <p className="text-sm text-text-muted mt-2">{indisponivel.serie_diaria}</p>
          ) : serie === null ? (
            <Skeleton className="h-[200px] rounded-lg mt-3" />
          ) : (
            <div className="mt-3" role="img" aria-label={`Faturamento diário de ${vendedor.vendedor}`}>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={serie} margin={CHART_THEME.margin}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
                  <XAxis dataKey="data" tickFormatter={formatarDataCurta} {...CHART_THEME.xAxis} />
                  <YAxis tickFormatter={(v: number) => `${(v / 1000).toLocaleString('pt-BR')}k`} {...CHART_THEME.yAxis} width={40} />
                  <Tooltip
                    contentStyle={CHART_THEME.tooltip.contentStyle}
                    labelFormatter={((d: string) => formatarDataCurta(d)) as never}
                    formatter={((v: number) => [formatCurrency(v), 'Faturamento']) as never}
                  />
                  <Line type="monotone" dataKey="faturamento_bruto" stroke="var(--color-primary)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        <section>
          <SectionHeader icon={Users}>O que vende ({rotulo('grupo')} / {rotulo('familia')})</SectionHeader>
          {indisponivel.mix_categoria ? (
            <p className="text-sm text-text-muted mt-2">{indisponivel.mix_categoria}</p>
          ) : mix === null ? (
            <Skeleton className="h-24 rounded-lg mt-3" />
          ) : mix.length === 0 ? (
            <p className="text-sm text-text-muted mt-2">Nenhuma venda no período.</p>
          ) : (
            <div className="flex flex-col gap-2 mt-3">
              {mix.slice(0, 8).map((m) => (
                <div key={`${m.grupo}-${m.familia}`} className="flex flex-col gap-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-text-primary">{m.familia || m.grupo || 'Sem categoria'}</span>
                    <span className="text-text-secondary">{formatCurrency(m.receita)} · {formatarPercentual(m.participacao)}</span>
                  </div>
                  <ProgressBar value={m.participacao} max={1} />
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </Modal>
  )
}

export default function Equipe() {
  const [periodo, setPeriodo] = useState<PeriodoBi>(periodoInicial)
  const [dados, setDados] = useState<ResultadoEquipe | null>(null)
  const [loading, setLoading] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [selecionado, setSelecionado] = useState<IndicadoresVendedor | null>(null)
  const [importados, setImportados] = useState<PeriodoBi[]>([])
  const [evolucao, setEvolucao] = useState<PontoMensal[] | null>(null)
  const { temModulo } = usePerfilEmpresa()
  const podeImportar = temModulo('importacao')

  const buscar = useCallback(async (p: PeriodoBi) => {
    setErro(null)
    setLoading(true)
    try {
      setDados(await fetchEquipe(p))
    } catch (e: unknown) {
      const detalhe = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setErro(typeof detalhe === 'string' ? detalhe : 'Erro ao carregar a equipe.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelado = false
    const inicial = podeImportar
      ? listarDatasets().then(periodosImportados).catch(() => [] as PeriodoBi[])
      : Promise.resolve([] as PeriodoBi[])
    inicial.then((periodos) => {
      if (cancelado) return
      setImportados(periodos)
      const escolhido = periodos[0] ?? periodoInicial()
      setPeriodo(escolhido)
      buscar(escolhido)
    })
    return () => { cancelado = true }
  }, [buscar, podeImportar])

  const fimDaBusca = dados?.periodo.fim
  useEffect(() => {
    if (!fimDaBusca) return
    let cancelado = false
    fetchSerieMensal(fimDaBusca).then((pontos) => { if (!cancelado) setEvolucao(pontos) }).catch(() => { if (!cancelado) setEvolucao(null) })
    return () => { cancelado = true }
  }, [fimDaBusca])

  function escolherPeriodo(p: PeriodoBi) {
    setPeriodo(p)
    buscar(p)
  }

  const colunasBase: Column<IndicadoresVendedor>[] = [
    {
      key: 'vendedor', label: 'Vendedor', align: 'left', headerAlign: 'left',
      render: (v) => (
        <span className={v.sem_vendedor ? 'italic text-text-muted' : 'font-medium text-text-primary'}>
          {v.vendedor}
          {v.novo && <span className="ml-2 text-[10px] font-semibold uppercase tracking-wide text-primary bg-primary-light px-1.5 py-0.5 rounded">novo</span>}
        </span>
      ),
    },
    {
      key: 'faturamento_liquido', label: 'Faturamento líquido', align: 'right',
      render: (v) => (
        <div className="flex flex-col items-end">
          <span>{formatCurrency(v.faturamento_liquido)}</span>
          {v.variacao_liquido !== null && <Variacao valor={v.variacao_liquido} />}
        </div>
      ),
    },
    { key: 'atendimentos', label: 'Atendimentos', align: 'right', hide: 'sm', render: (v) => v.atendimentos.toLocaleString('pt-BR') },
    { key: 'ticket_medio', label: 'Ticket médio', align: 'right', render: (v) => formatCurrency(v.ticket_medio) },
    { key: 'pa', label: 'PA', align: 'right', render: (v) => formatarDecimal(v.pa) },
    { key: 'preco_medio_peca', label: 'Preço médio/peça', align: 'right', hide: 'md', render: (v) => formatCurrency(v.preco_medio_peca) },
    { key: 'trocas', label: 'Trocas', align: 'right', hide: 'md', render: (v) => formatarPercentual(taxaDeTroca(v)) },
    { key: 'participacao', label: 'Participação', align: 'right', hide: 'sm', render: (v) => formatarPercentual(v.participacao) },
  ]
  if (dados?.vendedores.some((v) => v.conversao != null)) {
    colunasBase.push({
      key: 'conversao', label: 'Conversão', align: 'right', hide: 'md',
      render: (v) => v.conversao == null ? '—' : (
        <span title={`${v.atendimentos} atendimentos de ${v.contatos} contatos`}>{formatarPercentual(v.conversao)}</span>
      ),
    })
  }
  const temMetas = Boolean(dados?.vendedores.some((v) => v.meta !== null))
  const colunas = temMetas
    ? colunasBase.filter((c) => !['preco_medio_peca', 'participacao', 'trocas'].includes(c.key))
    : colunasBase
  if (temMetas) {
    colunas.push(
      {
        key: 'atingimento', label: 'Meta', align: 'right',
        render: (v) => v.meta === null || v.atingimento === null ? <span className="text-text-muted">—</span> : (
          <div className="flex flex-col gap-1 items-end w-20" title={`${formatarPercentual(v.atingimento, 0)} de ${formatCurrency(v.meta)}`}>
            <span className="text-xs text-text-secondary">{formatarPercentual(v.atingimento, 0)}</span>
            <div className="w-full"><ProgressBar value={Math.min(v.atingimento, 1)} max={1} /></div>
          </div>
        ),
      },
      {
        key: 'comissao_estimada', label: 'Comissão', align: 'right', hide: 'md',
        render: (v) => v.comissao_estimada === null ? '—' : formatCurrency(v.comissao_estimada),
      },
    )
  }

  const vendedores = dados?.vendedores ?? []

  return (
    <BiPageLayout
      titulo="Equipe de vendas"
      subtitulo="Desempenho por vendedor no período"
      breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Equipe' }]}
    >
      <Card variant="bordered">
        <div className="flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={(p) => buscar(p ?? periodo)} loading={loading} presets={PRESETS} />
          {importados.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-text-muted">Períodos importados:</span>
              {importados.map((p) => {
                const ativo = p.data_inicio === periodo.data_inicio && p.data_fim === periodo.data_fim
                return (
                  <button
                    key={`${p.data_inicio}-${p.data_fim}`}
                    onClick={() => escolherPeriodo(p)}
                    className={`text-xs px-2 py-1 rounded-md border transition ${ativo ? 'border-primary text-primary bg-primary-light' : 'border-border text-text-secondary hover:border-primary'}`}
                  >
                    {formatarDataCurta(p.data_inicio)} a {formatarDataCurta(p.data_fim)}
                  </button>
                )
              })}
            </div>
          )}
          {erro && <ErrorBanner message={erro} />}
        </div>
      </Card>

      {loading && !dados && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
      )}

      {dados && vendedores.length === 0 && !loading && (
        <EmptyState
          title="Nenhuma venda no período"
          description="Escolha outro período ou importe um relatório de vendas por vendedor que cubra estas datas."
        />
      )}

      {dados && vendedores.length > 0 && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <KpiCard label="Faturamento líquido" value={formatCurrency(dados.loja.faturamento_liquido)} />
            <KpiCard label="Atendimentos" value={dados.loja.atendimentos.toLocaleString('pt-BR')} />
            <KpiCard label="Ticket médio" value={formatCurrency(dados.loja.ticket_medio)} />
            <KpiCard label="Peças por atendimento" value={formatarDecimal(dados.loja.pa)} />
          </div>

          {textoDeComparacao(dados.periodo_anterior, dados.comparacao_parcial) && (
            <p className="text-xs text-text-muted flex items-center gap-1">
              <Info size={12} /> {textoDeComparacao(dados.periodo_anterior, dados.comparacao_parcial)}
            </p>
          )}

          {dados.equipe && (
            <Card variant="bordered">
              <SectionHeader icon={Users}>A equipe no período</SectionHeader>
              <div className="flex flex-wrap gap-x-8 gap-y-2 mt-3 text-sm text-text-secondary">
                <span>
                  <strong className="text-text-primary">{dados.equipe.vendedores_ativos}</strong> vendedores ativos
                  {dados.equipe.vendedores_ativos_anterior !== null && ` (${dados.equipe.vendedores_ativos_anterior} no período anterior)`}
                </span>
                {dados.equipe.concentracao_top3 !== null && (
                  <span><strong className="text-text-primary">{formatarPercentual(dados.equipe.concentracao_top3, 0)}</strong> do faturamento nos 3 maiores</span>
                )}
                {dados.equipe.entradas.length > 0 && (
                  <span className="inline-flex items-center gap-1"><UserPlus size={14} className="text-success" /> Entraram: {dados.equipe.entradas.join(', ')}</span>
                )}
                {dados.equipe.saidas.length > 0 && (
                  <span className="inline-flex items-center gap-1"><UserMinus size={14} className="text-danger" /> Não venderam neste período: {dados.equipe.saidas.join(', ')}</span>
                )}
              </div>
            </Card>
          )}

          {evolucao && pontosDaEvolucao(evolucao) >= 2 && (
            <Card variant="bordered">
              <SectionHeader icon={TrendingUp}>Evolução mensal da equipe</SectionHeader>
              <div className="mt-3">
                <EvolucaoMensal pontos={evolucao} descricao="Faturamento líquido mensal da equipe" mostrarAtivos />
              </div>
            </Card>
          )}

          {dados.loja.meta !== null && dados.loja.atingimento !== null && (
            <Card variant="bordered">
              <div className="flex flex-col gap-2">
                <div className="flex flex-wrap justify-between gap-2 text-sm">
                  <span className="text-text-primary font-medium">
                    Meta da loja: {formatarPercentual(dados.loja.atingimento, 0)} de {formatCurrency(dados.loja.meta)}
                  </span>
                  {dados.loja.projecao !== null && (
                    <span className="text-text-secondary">
                      Projeção do mês: {formatCurrency(dados.loja.projecao)} ({formatarPercentual(dados.loja.projecao / dados.loja.meta, 0)} da meta)
                    </span>
                  )}
                </div>
                <ProgressBar value={Math.min(dados.loja.atingimento, 1)} max={1} />
              </div>
            </Card>
          )}

          {dados.loja.atendimentos_somados_por_vendedor && (
            <p className="text-xs text-text-muted flex items-center gap-1">
              <Info size={12} /> Atendimentos da loja somados por vendedor: um atendimento com dois vendedores conta para os dois.
            </p>
          )}

          <Card variant="bordered">
            <SectionHeader icon={Users}>Ranking da equipe</SectionHeader>
            <DataTable
              data={vendedores}
              columns={colunas}
              rowKey={(v) => v.vendedor}
              onRowClick={setSelecionado}
            />
          </Card>

          <Card variant="bordered">
            <SectionHeader icon={TrendingUp}>Participação no faturamento</SectionHeader>
            <div className="mt-3" role="img" aria-label="Participação de cada vendedor no faturamento bruto">
              <ResponsiveContainer width="100%" height={Math.max(160, vendedores.length * 34)}>
                <BarChart data={vendedores} layout="vertical" margin={{ top: 2, right: 16, left: 8, bottom: 2 }} barCategoryGap={6}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--color-border)" />
                  <XAxis type="number" tickFormatter={(v: number) => formatarPercentual(v, 0)} tick={CHART_THEME.yAxis.tick} axisLine={false} tickLine={false} dataKey="participacao" />
                  <YAxis type="category" dataKey="vendedor" width={130} tick={CHART_THEME.yAxis.tick} axisLine={false} tickLine={false} />
                  <Tooltip cursor={CHART_THEME.tooltip.cursor} content={<TooltipParticipacao />} />
                  <Bar dataKey="participacao" fill="var(--color-primary)" radius={[0, 4, 4, 0]} maxBarSize={16} onClick={(d: unknown) => setSelecionado((d as { payload: IndicadoresVendedor }).payload)} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </>
      )}

      {selecionado && dados && (
        <DetalheVendedor vendedor={selecionado} periodo={periodo} resultado={dados} onClose={() => setSelecionado(null)} />
      )}
    </BiPageLayout>
  )
}
