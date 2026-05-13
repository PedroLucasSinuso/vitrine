import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { RefreshCw, Tags, ClipboardList, Users, Settings, Search, BarChart3, Sun, Moon, LogOut } from 'lucide-react'

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

  const [dark, setDark] = useState(() => localStorage.getItem('darkMode') === 'true')

  const logoUrl = localStorage.getItem('marketLogoUrl')
  const marketName = localStorage.getItem('marketName')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('darkMode', String(dark))
  }, [dark])

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
      <div className="w-full max-w-md flex flex-col gap-8">

        {/* Header */}
        <div className="flex justify-between items-center">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <img src="/vitrine_logo.svg" alt="Vitrine" className="h-7 w-auto shrink-0" />
              {logoUrl ? (
                <img src={logoUrl} alt={marketName ?? 'Logo'} className="h-12 w-auto rounded shrink-0" />
              ) : (
                <div className="w-12 h-12 rounded-lg bg-primary flex items-center justify-center text-white font-bold shrink-0">
                  {marketName ? marketName.charAt(0).toUpperCase() : 'M'}
                </div>
              )}
              {marketName && (
                <h1 className="text-sm font-semibold text-gray-800 dark:text-gray-100 truncate">{marketName}</h1>
              )}
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{getNomeExibicao()}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setDark((prev) => !prev)}
              className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
              aria-label="Alternar tema"
              title={dark ? 'Modo claro' : 'Modo escuro'}
            >
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="text-sm text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>

        {/* Cards */}
        <div className="flex flex-col gap-3">
          {CARDS.map((card) => {
            const Icon = card.icon
            return (
              <button
                key={card.path}
                onClick={() => navigate(card.path)}
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 text-left hover:shadow-md hover:ring-1 hover:ring-primary-lighter dark:hover:ring-primary transition flex items-start gap-4"
              >
                <div className="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center shrink-0">
                  <Icon size={22} className="text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-gray-800 dark:text-gray-100">{card.label}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{card.desc}</p>
                </div>
              </button>
            )
          })}
        </div>

        {/* Cards admin / supervisor / operador */}
        {(role === 'admin' || role === 'supervisor' || role === 'operador') && (
          <div>
            <h2 className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">Administração</h2>
            <div className="flex flex-col gap-3">
              {ADMIN_CARDS.filter(c => role === 'admin' || (role === 'operador' ? c.path === '/admin/inventario' : ['/admin/etiquetas', '/admin/inventario'].includes(c.path))).map((card) => {
                const Icon = card.icon
                return (
                  <button
                    key={card.path}
                    onClick={() => navigate(card.path)}
                    className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 text-left hover:shadow-md hover:ring-1 hover:ring-primary-lighter dark:hover:ring-primary transition flex items-start gap-4"
                  >
                    <div className="w-10 h-10 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center shrink-0">
                      <Icon size={22} className="text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800 dark:text-gray-100">{card.label}</p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{card.desc}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
