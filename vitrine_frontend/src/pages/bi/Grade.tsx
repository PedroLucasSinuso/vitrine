import { useCallback, useEffect, useState } from 'react'
import { format, startOfMonth } from 'date-fns'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Grid3x3, Palette, Ruler } from 'lucide-react'
import BiPageLayout from '../../components/bi/BiPageLayout'
import PeriodoForm, { type Preset } from '../../components/bi/PeriodoForm'
import Card from '../../components/ui/Card'
import EmptyState from '../../components/ui/EmptyState'
import ErrorBanner from '../../components/ui/ErrorBanner'
import SectionHeader from '../../components/ui/SectionHeader'
import { fetchGrade } from '../../api/equipe'
import { CHART_THEME } from '../../config/chartTheme'
import { usePerfilEmpresa } from '../../stores/perfilEmpresaContexto'
import type { ItemGrade, PeriodoBi, ResultadoGrade } from '../../types'
import { formatCurrency } from '../../utils/formatters'
import { formatarPercentual, intensidade } from '../../utils/equipe'

const PRESETS: Preset[] = [
  { label: 'Este mês', kind: 'current_month' },
  { label: 'Mês passado', kind: 'last_month' },
  { label: '30 dias', kind: 'days', days: 30 },
]

function TooltipGrade({ active, payload }: { active?: boolean; payload?: { payload: ItemGrade }[] }) {
  if (!active || !payload?.length) return null
  const item = payload[0].payload
  return (
    <div style={CHART_THEME.tooltip.contentStyle} className="px-3 py-2">
      <p className="font-semibold text-text-primary">{item.rotulo}</p>
      <p className="text-text-secondary">{item.quantidade.toLocaleString('pt-BR')} peças · {formatarPercentual(item.participacao)}</p>
      <p className="text-text-secondary">{formatCurrency(item.receita)}</p>
    </div>
  )
}

function Barras({ dados, rotulo }: { dados: ItemGrade[]; rotulo: string }) {
  return (
    <div role="img" aria-label={`Peças vendidas por ${rotulo}`}>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={dados} margin={CHART_THEME.margin}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
          <XAxis dataKey="rotulo" tick={CHART_THEME.yAxis.tick} axisLine={{ stroke: 'var(--color-border)' }} tickLine={false} interval={0} />
          <YAxis tick={CHART_THEME.yAxis.tick} axisLine={false} tickLine={false} width={36} />
          <Tooltip cursor={CHART_THEME.tooltip.cursor} content={<TooltipGrade />} />
          <Bar dataKey="quantidade" fill="var(--color-primary)" radius={[4, 4, 0, 0]} maxBarSize={36} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function MapaDeCalor({ grade }: { grade: ResultadoGrade }) {
  const celulas = new Map(grade.matriz.map((c) => [`${c.tamanho}|${c.cor}`, c.quantidade]))
  const maximo = Math.max(0, ...grade.matriz.map((c) => c.quantidade))
  return (
    <div className="overflow-x-auto">
      <table className="text-xs border-separate" style={{ borderSpacing: 2 }}>
        <caption className="sr-only">Peças vendidas por tamanho e cor</caption>
        <thead>
          <tr>
            <th className="px-2 py-1 text-left text-text-muted font-medium">Cor / tamanho</th>
            {grade.tamanhos.map((t) => <th key={t} scope="col" className="px-2 py-1 text-text-muted font-medium">{t}</th>)}
          </tr>
        </thead>
        <tbody>
          {grade.cores.map((cor) => (
            <tr key={cor}>
              <th scope="row" className="px-2 py-1 text-left text-text-secondary font-medium whitespace-nowrap">{cor}</th>
              {grade.tamanhos.map((tamanho) => {
                const quantidade = celulas.get(`${tamanho}|${cor}`) ?? 0
                const nivel = intensidade(quantidade, maximo)
                return (
                  <td
                    key={tamanho}
                    title={`${cor}, ${tamanho}: ${quantidade.toLocaleString('pt-BR')} peças`}
                    className={`min-w-[44px] h-9 text-center rounded ${nivel > 72 ? 'text-white' : 'text-text-primary'}`}
                    style={{ background: nivel ? `color-mix(in srgb, var(--color-primary) ${nivel}%, var(--color-bg-card))` : 'var(--color-bg-hover)' }}
                  >
                    {quantidade ? quantidade.toLocaleString('pt-BR') : ''}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-text-muted mt-2">Quanto mais intensa a cor da célula, mais peças vendidas naquele tamanho e cor.</p>
    </div>
  )
}

export default function Grade() {
  const { rotulo } = usePerfilEmpresa()
  const [periodo, setPeriodo] = useState<PeriodoBi>(() => ({
    data_inicio: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
    data_fim: format(new Date(), 'yyyy-MM-dd'),
  }))
  const [grupo, setGrupo] = useState('')
  const [familia, setFamilia] = useState('')
  const [dados, setDados] = useState<ResultadoGrade | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(false)

  const buscar = useCallback(async (p: PeriodoBi, g: string, f: string) => {
    setErro(null)
    setCarregando(true)
    try {
      setDados(await fetchGrade(p, g, f))
    } catch (e: unknown) {
      const detalhe = (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setErro(typeof detalhe === 'string' ? detalhe : 'Erro ao carregar a grade.')
      setDados(null)
    } finally {
      setCarregando(false)
    }
  }, [])

  const [periodoBuscado, setPeriodoBuscado] = useState(periodo)

  useEffect(() => {
    const t = setTimeout(() => buscar(periodoBuscado, grupo, familia))
    return () => clearTimeout(t)
  }, [buscar, periodoBuscado, grupo, familia])

  return (
    <BiPageLayout titulo="Grade" subtitulo="O que sai por tamanho e cor" breadcrumb={[{ label: 'BI', path: '/bi' }, { label: 'Grade' }]}>
      <Card variant="bordered">
        <div className="flex flex-col gap-4">
          <PeriodoForm value={periodo} onChange={setPeriodo} onBuscar={(p) => setPeriodoBuscado({ ...(p ?? periodo) })} loading={carregando} presets={PRESETS} />
          <div className="flex flex-wrap gap-4">
            <label className="flex flex-col gap-1 text-xs text-text-muted">
              {rotulo('grupo')}
              <select className="form-input-base" value={grupo} onChange={(e) => { setGrupo(e.target.value); setFamilia('') }}>
                <option value="">Todos</option>
                {dados?.grupos.map((g) => <option key={g} value={g}>{g}</option>)}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs text-text-muted">
              {rotulo('familia')}
              <select className="form-input-base" value={familia} onChange={(e) => setFamilia(e.target.value)}>
                <option value="">Todas</option>
                {dados?.familias.map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
            </label>
          </div>
          {erro && <ErrorBanner message={erro} />}
        </div>
      </Card>

      {dados && dados.total_pecas === 0 && (
        <EmptyState title="Nenhuma peça vendida no período" description="Escolha outro período ou filtro." />
      )}

      {dados && dados.total_pecas > 0 && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card variant="bordered">
              <SectionHeader icon={Ruler}>Por tamanho</SectionHeader>
              <Barras dados={dados.por_tamanho} rotulo="tamanho" />
            </Card>
            <Card variant="bordered">
              <SectionHeader icon={Palette}>Por cor</SectionHeader>
              <Barras dados={dados.por_cor} rotulo="cor" />
            </Card>
          </div>
          <Card variant="bordered">
            <SectionHeader icon={Grid3x3}>Tamanho × cor</SectionHeader>
            <div className="mt-3"><MapaDeCalor grade={dados} /></div>
          </Card>
        </>
      )}
    </BiPageLayout>
  )
}
