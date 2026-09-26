import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { format, startOfMonth } from 'date-fns'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Info, Percent, Target, TrendingUp, Users } from 'lucide-react'
import BiPageLayout from '../../components/bi/BiPageLayout'
import EvolucaoMensal from '../../components/bi/EvolucaoMensal'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import Card from '../../components/ui/Card'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import KpiCard from '../../components/ui/KpiCard'
import ProgressBar from '../../components/ui/ProgressBar'
import SectionHeader from '../../components/ui/SectionHeader'
import Skeleton from '../../components/ui/Skeleton'
import { fetchDetalheVendedor } from '../../api/equipe'
import { CHART_THEME } from '../../config/chartTheme'
import { usePerfilEmpresa } from '../../stores/perfilEmpresaContexto'
import type { ComparacaoComLoja, DetalheVendedor, PeriodoBi } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import {
  direcaoVariacao, formatarDataCurta, formatarDecimal, formatarPercentual, formatarVariacao,
  pontosDaEvolucao, posicaoEmTexto, taxaDeTroca, textoDeComparacao,
} from '../../utils/equipe'

const PRESETS: Preset[] = [
  { label: 'Este mês', kind: 'current_month' },
  { label: 'Mês passado', kind: 'last_month' },
  { label: '30 dias', kind: 'days', days: 30 },
]

function periodoDaUrl(params: URLSearchParams): PeriodoBi {
  return {
    data_inicio: params.get('inicio') ?? format(startOfMonth(new Date()), 'yyyy-MM-dd'),
    data_fim: params.get('fim') ?? format(new Date(), 'yyyy-MM-dd'),
  }
}

function Variacao({ valor }: { valor: number | null | undefined }) {
  if (valor === null || valor === undefined) return null
  const direcao = direcaoVariacao(valor)
  const classe = direcao === 'positivo' ? 'text-success' : direcao === 'negativo' ? 'text-danger' : 'text-text-muted'
  return <span className={`text-xs font-medium ${classe}`}>{direcao === 'positivo' ? '▲ ' : direcao === 'negativo' ? '▼ ' : ''}{formatarVariacao(valor)}</span>
}

const ROTULOS_COMPARACAO: { chave: keyof ComparacaoComLoja; rotulo: string; menorEMelhor?: boolean }[] = [
  { chave: 'ticket_medio', rotulo: 'Ticket médio' },
  { chave: 'pa', rotulo: 'Peças por atendimento' },
  { chave: 'preco_medio_peca', rotulo: 'Preço médio por peça' },
  { chave: 'taxa_troca', rotulo: 'Taxa de troca', menorEMelhor: true },
]

function ComparacaoLoja({ comparacao }: { comparacao: ComparacaoComLoja }) {
  const itens = ROTULOS_COMPARACAO.filter((i) => comparacao[i.chave] !== null)
  if (itens.length === 0) return null
  return (
    <Card variant="bordered">
      <SectionHeader icon={Users}>Comparado à média da loja</SectionHeader>
      <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
        {itens.map(({ chave, rotulo, menorEMelhor }) => {
          const valor = comparacao[chave] as number
          const bom = menorEMelhor ? valor <= 0 : valor >= 0
          return (
            <li key={chave} className="rounded-lg border border-border p-3">
              <p className="text-xs text-text-muted">{rotulo}</p>
              <p className={`text-lg font-semibold ${Math.abs(valor) < 0.005 ? 'text-text-primary' : bom ? 'text-success' : 'text-danger'}`}>
                {formatarVariacao(valor)}
              </p>
              <p className="text-xs text-text-muted">{valor >= 0 ? 'acima' : 'abaixo'} da média</p>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}

function Conteudo({ dados }: { dados: DetalheVendedor }) {
  const { rotulo } = usePerfilEmpresa()
  const v = dados.indicadores
  const nota = textoDeComparacao(dados.periodo_anterior, dados.comparacao_parcial)
  const evolucaoTemDados = pontosDaEvolucao(dados.serie_mensal) >= 2
  return (
    <>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <KpiCard label="Faturamento líquido" value={formatCurrency(v.faturamento_liquido)} />
        <KpiCard label="Atendimentos" value={v.atendimentos.toLocaleString('pt-BR')} />
        <KpiCard label="Ticket médio" value={formatCurrency(v.ticket_medio)} />
        <KpiCard label="Peças por atendimento" value={formatarDecimal(v.pa)} />
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-text-secondary">
        {v.variacao_liquido !== null && <span>Faturamento líquido vs período anterior: <Variacao valor={v.variacao_liquido} /></span>}
        {v.variacao_ticket_medio !== null && <span>Ticket médio vs anterior: <Variacao valor={v.variacao_ticket_medio} /></span>}
        {v.variacao_pa !== null && <span>PA vs anterior: <Variacao valor={v.variacao_pa} /></span>}
        <span>Taxa de troca: {formatarPercentual(taxaDeTroca(v))}</span>
        <span>Participação na loja: {formatarPercentual(v.participacao)}</span>
      </div>
      {nota && (
        <p className="text-xs text-text-muted flex items-center gap-1"><Info size={12} /> {nota}</p>
      )}

      <ComparacaoLoja comparacao={dados.comparacao_loja} />

      {v.meta !== null && v.atingimento !== null && (
        <Card variant="bordered">
          <SectionHeader icon={Target}>Meta do mês</SectionHeader>
          <div className="flex flex-col gap-2 mt-3">
            <div className="flex flex-wrap justify-between gap-2 text-sm">
              <span className="text-text-primary font-medium">{formatarPercentual(v.atingimento, 0)} de {formatCurrency(v.meta)}</span>
              {v.projecao !== null && <span className="text-text-secondary">Projeção do mês: {formatCurrency(v.projecao)}</span>}
              {v.comissao_estimada !== null && <span className="text-text-secondary">Comissão estimada: {formatCurrency(v.comissao_estimada)}</span>}
            </div>
            <ProgressBar value={Math.min(v.atingimento, 1)} max={1} />
          </div>
        </Card>
      )}

      {v.conversao != null && v.contatos != null && (
        <Card variant="bordered">
          <SectionHeader icon={Percent}>Conversão de contatos</SectionHeader>
          <p className="text-sm text-text-secondary mt-2">
            {v.atendimentos.toLocaleString('pt-BR')} atendimentos para {v.contatos.toLocaleString('pt-BR')} contatos:{' '}
            <strong className="text-text-primary">{formatarPercentual(v.conversao)}</strong>
          </p>
        </Card>
      )}

      {evolucaoTemDados && dados.serie_mensal && (
        <Card variant="bordered">
          <SectionHeader icon={TrendingUp}>Evolução mensal</SectionHeader>
          <div className="mt-3">
            <EvolucaoMensal pontos={dados.serie_mensal} descricao={`Faturamento líquido mensal de ${v.vendedor}`} />
          </div>
        </Card>
      )}

      {dados.serie_diaria && dados.serie_diaria.length > 0 && (
        <Card variant="bordered">
          <SectionHeader icon={TrendingUp}>Evolução diária</SectionHeader>
          <div className="mt-3" role="img" aria-label={`Faturamento diário de ${v.vendedor}`}>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={dados.serie_diaria} margin={CHART_THEME.margin}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
                <XAxis dataKey="data" tickFormatter={formatarDataCurta} {...CHART_THEME.xAxis} />
                <YAxis tickFormatter={(x: number) => `${(x / 1000).toLocaleString('pt-BR')}k`} {...CHART_THEME.yAxis} width={40} />
                <Tooltip contentStyle={CHART_THEME.tooltip.contentStyle} labelFormatter={((d: string) => formatarDataCurta(d)) as never} formatter={((x: number) => [formatCurrency(x), 'Faturamento']) as never} />
                <Line type="monotone" dataKey="faturamento_bruto" stroke="var(--color-primary)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}

      {dados.mix && dados.mix.length > 0 && (
        <Card variant="bordered">
          <SectionHeader icon={Users}>O que vende ({rotulo('grupo')} / {rotulo('familia')})</SectionHeader>
          <div className="flex flex-col gap-2 mt-3">
            {dados.mix.slice(0, 8).map((m) => (
              <div key={`${m.grupo}-${m.familia}`} className="flex flex-col gap-1">
                <div className="flex justify-between text-sm">
                  <span className="text-text-primary">{m.familia || m.grupo || 'Sem categoria'}</span>
                  <span className="text-text-secondary">{formatCurrency(m.receita)} · {formatarPercentual(m.participacao)}</span>
                </div>
                <ProgressBar value={m.participacao} max={1} />
              </div>
            ))}
          </div>
        </Card>
      )}

      {dados.indisponivel.length > 0 && (
        <p className="text-xs text-text-muted">
          Para ampliar esta análise: {dados.indisponivel.map((i) => i.motivo.replace(/\.$/, '').toLowerCase()).join('; ')}.
        </p>
      )}
    </>
  )
}

export default function Vendedor() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const nome = params.get('nome') ?? ''
  const [periodo, setPeriodo] = useState<PeriodoBi>(() => periodoDaUrl(params))
  const [dados, setDados] = useState<DetalheVendedor | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(false)

  const buscar = useCallback(async (p: PeriodoBi) => {
    setErro(null)
    setCarregando(true)
    try {
      setDados(await fetchDetalheVendedor(p, nome))
    } catch (e: unknown) {
      const status = (e as { response?: { status?: number } }).response?.status
      setDados(null)
      setErro(status === 404 ? 'Este vendedor não tem vendas no período escolhido.' : 'Erro ao carregar o vendedor.')
    } finally {
      setCarregando(false)
    }
  }, [nome])

  useEffect(() => {
    if (!nome) return
    const t = setTimeout(() => buscar(periodoDaUrl(params)))
    return () => clearTimeout(t)
  }, [buscar, nome, params])

  function aplicar(p: PeriodoBi) {
    setPeriodo(p)
    setParams({ nome, inicio: p.data_inicio, fim: p.data_fim }, { replace: true })
  }

  const posicao = dados ? posicaoEmTexto(dados.posicao, dados.total_vendedores) : null

  return (
    <BiPageLayout
      titulo={nome || 'Vendedor'}
      subtitulo={posicao ? `${posicao} no ranking do período${dados?.indicadores.novo ? ' · novo na equipe' : ''}` : 'Desempenho individual'}
      breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Equipe', path: '/bi/equipe' }, { label: nome || 'Vendedor' }]}
    >
      <Card variant="bordered">
        <div className="flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={(p) => aplicar(p ?? periodo)} loading={carregando} presets={PRESETS} />
          {erro && <ErrorBanner message={erro} />}
        </div>
      </Card>

      {!nome && (
        <EmptyState title="Nenhum vendedor escolhido" description="Abra um vendedor a partir do ranking da equipe." action={<button className="text-primary underline text-sm" onClick={() => navigate('/bi/equipe')}>Ir para a equipe</button>} />
      )}
      {carregando && !dados && <Skeleton className="h-24 rounded-xl" />}
      {dados && <Conteudo dados={dados} />}
    </BiPageLayout>
  )
}
