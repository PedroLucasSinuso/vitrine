import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Card from '../components/ui/Card'
import { RefreshCw, Tags, ClipboardList, Users, Settings, Search, BarChart3, LogOut } from 'lucide-react'

const ADMIN_CARDS = [
  { label: 'Sync', desc: 'Sincronização ETL', path: '/admin', icon: RefreshCw },
  { label: 'Etiquetas', desc: 'Gerenciar etiquetas de produtos', path: '/admin/etiquetas', icon: Tags },
  { label: 'Inventário', desc: 'Contagem de inventário', path: '/admin/inventario', icon: ClipboardList },
  { label: 'Usuários', desc: 'Gerenciar usuários do sistema', path: '/admin/usuarios', icon: Users },
  { label: 'Configurações', desc: 'Configurações do sistema', path: '/admin/configuracoes', icon: Settings },
]

const CARDS = [
  { label: 'Busca', desc: 'Consultar preço e estoque por código', path: '/busca', icon: Search },
  { label: 'BI', desc: 'Relatórios e análises de vendas', path: '/bi', icon: BarChart3 },
]

export default function Home() {
  const navigate = useNavigate()
  const { logout, getRole, getNomeExibicao } = useAuth()
  const role = getRole()

  const logoUrl = localStorage.getItem('app_marketLogoUrl')
  const marketName = localStorage.getItem('app_marketName')

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-lg flex flex-col gap-8">

        {/* Header */}
        <div className="flex justify-between items-center">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <img src="/vitrine_logo.svg" alt="Vitrine" className="h-7 w-auto shrink-0" />
              {logoUrl ? (
                <img src={logoUrl} alt={marketName ?? 'Logo'} className="h-10 w-auto rounded-lg shrink-0" />
              ) : (
                <div className="w-9 h-9 rounded-lg bg-primary-light flex items-center justify-center text-primary font-bold shrink-0">
                  {marketName ? marketName.charAt(0).toUpperCase() : 'M'}
                </div>
              )}
              <div className="min-w-0">
                {marketName && (
                  <p className="text-sm font-semibold text-text-primary truncate leading-tight">{marketName}</p>
                )}
                <p className="text-xs text-text-muted truncate">{getNomeExibicao()}</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={handleLogout}
              className="text-text-muted hover:text-danger transition p-2 rounded-lg hover:bg-danger-light"
              aria-label="Sair"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>

        {/* Main cards */}
        <div className="flex flex-col gap-3">
          {CARDS.map((card) => {
            const Icon = card.icon
            return (
              <Card
                key={card.path}
                variant="interactive"
                onClick={() => navigate(card.path)}
                className="flex items-start gap-4"
              >
                <div className="w-11 h-11 rounded-xl bg-primary-light flex items-center justify-center shrink-0">
                  <Icon size={22} className="text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-text-primary">{card.label}</p>
                  <p className="text-xs text-text-muted mt-0.5">{card.desc}</p>
                </div>
              </Card>
            )
          })}
        </div>

        {/* Admin cards */}
        {(role === 'admin' || role === 'supervisor' || role === 'operador') && (
          <div>
            <div className="border-t border-border mb-3" />
            <h2 className="text-xs font-semibold text-text-muted uppercase tracking-wide mb-3">Administração</h2>
            <div className="flex flex-col gap-3">
              {ADMIN_CARDS.filter(c => role === 'admin' || (role === 'operador' ? c.path === '/admin/inventario' : ['/admin/etiquetas', '/admin/inventario'].includes(c.path))).map((card) => {
                const Icon = card.icon
                return (
                  <Card
                    key={card.path}
                    variant="interactive"
                    onClick={() => navigate(card.path)}
                    className="flex items-start gap-4"
                  >
                    <div className="w-11 h-11 rounded-xl bg-primary-light flex items-center justify-center shrink-0">
                      <Icon size={22} className="text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-text-primary">{card.label}</p>
                      <p className="text-xs text-text-muted mt-0.5">{card.desc}</p>
                    </div>
                  </Card>
                )
              })}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
