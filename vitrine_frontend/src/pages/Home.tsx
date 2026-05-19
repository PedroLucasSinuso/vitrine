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

  const [dark, setDark] = useState(() => localStorage.getItem('app_darkMode') === 'true')

  const logoUrl = localStorage.getItem('app_marketLogoUrl')
  const marketName = localStorage.getItem('app_marketName')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('app_darkMode', String(dark))
  }, [dark])

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-8 overflow-x-auto">
      <div className="w-full max-w-lg flex flex-col gap-8">

        {/* Header */}
        <div className="flex justify-between items-center">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <img src="/vitrine_logo.svg" alt="Vitrine" className="h-7 w-auto shrink-0 dark:invert" />
              {logoUrl ? (
                <img src={logoUrl} alt={marketName ?? 'Logo'} className="h-10 w-auto rounded-lg shrink-0" />
              ) : (
                <div className="w-10 h-10 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-primary font-bold shrink-0">
                  {marketName ? marketName.charAt(0).toUpperCase() : 'M'}
                </div>
              )}
              {marketName && (
                <h1 className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{marketName}</h1>
              )}
            </div>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{getNomeExibicao()}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setDark((prev) => !prev)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              aria-label="Alternar tema"
              title={dark ? 'Modo claro' : 'Modo escuro'}
              title={dark ? 'Modo claro' : 'Modo escuro'}
            >
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
              aria-label="Sair"
              title="Sair"
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
              <button
                key={card.path}
                onClick={() => navigate(card.path)}
                className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-5 text-left hover:shadow-md hover:border-primary/30 dark:hover:border-primary/30 transition flex items-start gap-4"
              >
                <div className="w-11 h-11 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center shrink-0">
                  <Icon size={22} className="text-primary" />
                </div>
                <div>
                  <p className="font-semibold text-slate-800 dark:text-slate-100">{card.label}</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">{card.desc}</p>
                </div>
              </button>
            )
          })}
        </div>

        {/* Admin cards */}
        {(role === 'admin' || role === 'supervisor' || role === 'operador') && (
          <div>
            <div className="border-t border-slate-200 dark:border-slate-700/50 mb-3" />
            <h2 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mb-3">Administração</h2>
            <div className="flex flex-col gap-3">
              {ADMIN_CARDS.filter(c => role === 'admin' || (role === 'operador' ? c.path === '/admin/inventario' : ['/admin/etiquetas', '/admin/inventario'].includes(c.path))).map((card) => {
                const Icon = card.icon
                return (
                  <button
                    key={card.path}
                    onClick={() => navigate(card.path)}
                    className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-5 text-left hover:shadow-md hover:border-primary/30 dark:hover:border-primary/30 transition flex items-start gap-4"
                  >
                    <div className="w-11 h-11 rounded-xl bg-primary/10 dark:bg-primary/20 flex items-center justify-center shrink-0">
                      <Icon size={22} className="text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-slate-800 dark:text-slate-100">{card.label}</p>
                      <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">{card.desc}</p>
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
