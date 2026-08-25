import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  BarChart3,
  Boxes,
  ClipboardList,
  Code2,
  LineChart,
  LogIn,
  Play,
  Search,
  Shield,
  Tags,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { demoDisponivel } from '../api/auth'
import Button from '../components/ui/Button'
import Logo from '../components/ui/Logo'

const REPO_URL = 'https://github.com/PedroLucasSinuso/vitrine'

const FUNCIONALIDADES = [
  {
    icon: LineChart,
    titulo: 'Dashboard de BI',
    texto:
      'Faturamento, ticket médio e itens por ticket, cada um comparado com o mesmo período do ano anterior. O dia corrente aparece marcado como parcial.',
  },
  {
    icon: BarChart3,
    titulo: 'Curva ABC e ranking',
    texto:
      'Classificação A/B/C por receita acumulada, ranking por receita ou quantidade, e receita quebrada por grupo e por família.',
  },
  {
    icon: LineChart,
    titulo: 'Análise temporal',
    texto:
      'Distribuição por hora do dia e por dia da semana — é onde os dois picos de movimento do supermercado aparecem.',
  },
  {
    icon: Boxes,
    titulo: 'Perdas, consumo e trocas',
    texto:
      'Três operações que saem do estoque sem virar receita, cada uma com total, taxa e detalhamento por produto.',
  },
  {
    icon: Search,
    titulo: 'Consulta de produto',
    texto:
      'Busca por EAN, PLU ou nome, com preço, custo, markup, margem e estoque. É a tela que fica no terminal de consulta da loja.',
  },
  {
    icon: ClipboardList,
    titulo: 'Inventário',
    texto:
      'Sessões de contagem por operador, com exportação do delta contra o estoque do sistema em Excel e TXT.',
  },
  {
    icon: Tags,
    titulo: 'Etiquetas',
    texto: 'Geração e impressão de etiquetas de gôndola a partir do catálogo sincronizado.',
  },
  {
    icon: Shield,
    titulo: 'Multi-tenant',
    texto:
      'Cada empresa tem seus dados, usuários e configurações isolados, com três perfis de acesso: admin, supervisor e operador.',
  },
]

const STACK = [
  { titulo: 'Backend', itens: 'FastAPI · SQLAlchemy 2.0 · Alembic · APScheduler · pytest' },
  { titulo: 'Frontend', itens: 'React 19 · TypeScript · Vite · Tailwind v4 · Recharts' },
  { titulo: 'Dados', itens: 'SQLite (aplicação) · PostgreSQL (ERP do cliente, somente leitura)' },
  { titulo: 'Infra', itens: 'Docker Compose · nginx · GitHub Actions' },
]

export default function Landing() {
  const navigate = useNavigate()
  const { entrarNaDemo } = useAuth()
  const [temDemo, setTemDemo] = useState(false)
  const [entrando, setEntrando] = useState(false)
  const [erro, setErro] = useState('')

  useEffect(() => {
    demoDisponivel().then(setTemDemo)
  }, [])

  async function abrirDemo() {
    setErro('')
    setEntrando(true)
    try {
      await entrarNaDemo()
      navigate('/bi', { replace: true })
    } catch {
      setErro('Não foi possível abrir a demonstração agora. Tente de novo em instantes.')
      setEntrando(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg-page relative overflow-hidden">
      {/* Mesma decoração de fundo da tela de login, para a landing e o
          sistema parecerem o mesmo produto. */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] bg-accent/5 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-5xl mx-auto px-6 py-10">
        <header className="flex items-center justify-between mb-20">
          <Logo height={28} className="text-text-primary" />
          <div className="flex items-center gap-2">
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 text-sm text-text-muted hover:text-text-primary transition-colors px-3 py-2"
            >
              <Code2 size={16} />
              <span className="hidden sm:inline">Código</span>
            </a>
            <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
              <LogIn size={15} />
              Entrar
            </Button>
          </div>
        </header>

        <section className="max-w-2xl mb-16">
          <h1 className="text-4xl sm:text-5xl font-bold text-text-primary leading-tight tracking-tight font-display mb-6">
            Gestão inteligente<br />
            <span className="text-primary">para o seu supermercado</span>
          </h1>
          <p className="text-text-secondary text-lg leading-relaxed mb-4">
            O Vitrine lê o ERP da loja e transforma o movimento do caixa em
            relatórios de BI, consulta de preço, inventário e etiquetas — sem
            planilha no meio do caminho.
          </p>
          <p className="text-text-muted leading-relaxed mb-8">
            O ERP entra por um adapter, então trocar de fornecedor é escrever
            uma implementação nova, não reescrever o sistema. A demonstração
            abaixo roda por esse mesmo mecanismo, com uma fonte de dados
            sintética no lugar do banco de um cliente.
          </p>

          <div className="flex flex-wrap items-center gap-3">
            {temDemo && (
              <Button size="lg" onClick={abrirDemo} loading={entrando}>
                <Play size={16} />
                Ver demonstração
              </Button>
            )}
            <Button variant="outline" size="lg" onClick={() => navigate('/login')}>
              Já tenho conta
            </Button>
          </div>

          {temDemo && (
            <p className="text-xs text-text-muted mt-4 max-w-lg">
              Entra direto, sem cadastro, com acesso de administrador. Os dados
              são gerados, não pertencem a nenhuma loja real, e o ambiente volta
              ao estado inicial sozinho — pode mexer à vontade.
            </p>
          )}

          {erro && (
            <div
              className="flex items-center gap-2 bg-danger-light border border-danger/20 rounded-lg px-3 py-2.5 text-sm text-danger mt-4 max-w-lg"
              role="alert"
            >
              <AlertCircle size={14} className="shrink-0" />
              {erro}
            </div>
          )}
        </section>

        <section className="mb-16">
          <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-6">
            O que tem dentro
          </h2>
          <div className="grid sm:grid-cols-2 gap-x-8 gap-y-7">
            {FUNCIONALIDADES.map(({ icon: Icon, titulo, texto }) => (
              <div key={titulo} className="flex gap-4">
                <div className="w-10 h-10 rounded-xl bg-primary-light flex items-center justify-center shrink-0">
                  <Icon size={18} className="text-primary" />
                </div>
                <div>
                  <p className="font-medium text-text-primary mb-1">{titulo}</p>
                  <p className="text-sm text-text-muted leading-relaxed">{texto}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mb-16">
          <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-6">
            Como é construído
          </h2>
          <div className="grid sm:grid-cols-2 gap-x-8 gap-y-5">
            {STACK.map(({ titulo, itens }) => (
              <div key={titulo}>
                <p className="text-sm font-medium text-text-primary mb-1">{titulo}</p>
                <p className="text-sm text-text-muted leading-relaxed">{itens}</p>
              </div>
            ))}
          </div>
        </section>

        <footer className="border-t border-border pt-6 pb-4 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-text-muted">
            Vitrine — Sistema de Gestão para Supermercados
          </p>
          <a
            href={REPO_URL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-xs text-text-muted hover:text-text-primary transition-colors"
          >
            <Code2 size={14} />
            Ver o código no GitHub
          </a>
        </footer>
      </div>
    </div>
  )
}
