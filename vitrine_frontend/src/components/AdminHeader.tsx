import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getConfigsCache } from '../stores/configStore'
import { RefreshCw, Tags, ClipboardList, Users, Settings, Search, BarChart3, Sun, Moon, ArrowLeft, ChevronRight, LogOut } from 'lucide-react'
import NotificationCenter from './NotificationCenter'
import type { LucideIcon } from 'lucide-react'

interface Breadcrumb {
  label: string
  path?: string
}

interface Props {
  titulo: string
  paginaAtual: 'sync' | 'etiquetas' | 'inventario' | 'busca' | 'usuarios' | 'bi' | 'configuracoes'
  breadcrumb?: Breadcrumb[]
  hideNav?: boolean
  onLogout?: () => void
}

interface Link {
  label: string
  icon: LucideIcon
  pagina: string
  path: string
}

const ADMIN_LINKS: Link[] = [
  { label: 'Sync', icon: RefreshCw, pagina: 'sync', path: '/admin' },
  { label: 'Etiquetas', icon: Tags, pagina: 'etiquetas', path: '/admin/etiquetas' },
  { label: 'Inventário', icon: ClipboardList, pagina: 'inventario', path: '/admin/inventario' },
  { label: 'Usuários', icon: Users, pagina: 'usuarios', path: '/admin/usuarios' },
  { label: 'Configurações', icon: Settings, pagina: 'configuracoes', path: '/admin/configuracoes' },
]

const COMMON_LINKS: Link[] = [
  { label: 'Busca', icon: Search, pagina: 'busca', path: '/busca' },
  { label: 'BI', icon: BarChart3, pagina: 'bi', path: '/bi' },
]

export default function AdminHeader({ titulo, paginaAtual, breadcrumb, hideNav, onLogout }: Props) {
  const navigate = useNavigate()
  const { logout, getRole, getNomeExibicao, getExpiresInMs } = useAuth()
  const role = getRole()

  const [dark, setDark] = useState(() => localStorage.getItem('app_darkMode') === 'true')
  const [menuOpen, setMenuOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const logoUrl = localStorage.getItem('app_marketLogoUrl')
  const marketName = localStorage.getItem('app_marketName')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('app_darkMode', String(dark))
  }, [dark])

  useEffect(() => {
    if (!menuOpen) return
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [menuOpen])

  useEffect(() => {
    getConfigsCache().catch(() => {})
  }, [])

  function handleLogout() {
    if (onLogout) { onLogout(); return }
    logout()
    navigate('/login')
  }

  const expiringMs = getExpiresInMs()
  const expiringMin = Math.ceil(expiringMs / 60000)
  const expiringBadge = expiringMs > 0 && expiringMs < 300000

  const isAdmin = role === 'admin'
  const isOperador = role === 'operador'
  const supervisorAdminLinks = ADMIN_LINKS.filter(l => l.pagina === 'etiquetas' || l.pagina === 'inventario')
  const operadorAdminLinks = ADMIN_LINKS.filter(l => l.pagina === 'inventario')
  const adminLinksToShow = isAdmin ? ADMIN_LINKS : isOperador ? operadorAdminLinks : supervisorAdminLinks
  const links = isAdmin ? [...ADMIN_LINKS, ...COMMON_LINKS] : isOperador ? [...operadorAdminLinks, ...COMMON_LINKS] : [...supervisorAdminLinks, ...COMMON_LINKS]
  const cols = 'grid-cols-3 sm:grid-cols-6'
  const logoFallback = marketName ? marketName.charAt(0).toUpperCase() : 'M'

  return (
    <div className="w-full max-w-5xl relative">
      {/* Breadcrumb */}
      {breadcrumb && breadcrumb.length > 0 && (
        <nav className="text-xs text-slate-400 dark:text-slate-400 mb-2 flex items-center gap-0.5 flex-wrap" aria-label="Breadcrumb">
          {breadcrumb.map((b, i) => (
            <span key={i} className="flex items-center gap-0.5">
              {i > 0 && <ChevronRight size={10} className="opacity-40" />}
              {b.path
                ? <button onClick={() => navigate(b.path!)} className="hover:text-primary dark:hover:text-primary-light transition font-medium">{b.label}</button>
                : <span className="text-slate-600 dark:text-slate-300 font-medium">{b.label}</span>
              }
            </span>
          ))}
        </nav>
      )}

      {/* Main header row — mobile: stacked, desktop: single row */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        {/* Left: branding + page info */}
        <div className="flex items-center gap-3 min-w-0">
          {hideNav && (
            <button
              onClick={() => setMenuOpen((prev) => !prev)}
              className="flex items-center gap-1 text-xs font-semibold text-primary dark:text-primary-light bg-white dark:bg-slate-800 rounded-xl px-3 py-2 shadow-sm hover:bg-primary-lighter dark:hover:bg-slate-700 transition whitespace-nowrap shrink-0"
              aria-label="Abrir navegação admin"
            >
              <ArrowLeft size={14} /> Admin
            </button>
          )}
          {/* Logo with dark mode invert */}
          <img src="/vitrine_logo.svg" alt="Vitrine" className="h-6 w-auto shrink-0 dark:invert" />
          {logoUrl ? (
            <img src={logoUrl} alt={marketName ?? 'Logo'} className="h-10 w-auto rounded-lg shrink-0" />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-primary font-bold shrink-0">
              {logoFallback}
            </div>
          )}
          <div className="min-w-0">
            {marketName && (
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate leading-tight">{marketName}</p>
            )}
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{titulo}</p>
          </div>
        </div>

        {/* Right: user actions */}
        <div className="flex items-center gap-2 shrink-0 sm:pl-3 sm:border-l sm:border-slate-200 sm:dark:border-slate-700">
          {expiringBadge && (
            <span className="hidden sm:inline-flex text-[10px] bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400 font-medium px-2 py-1 rounded-full border border-amber-200 dark:border-amber-800">
              Expira em {expiringMin}min
            </span>
          )}
          <NotificationCenter />
          <button
            onClick={() => setDark((prev) => !prev)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Alternar tema"
            title={dark ? 'Modo claro' : 'Modo escuro'}
          >
            {dark ? <Sun size={15} /> : <Moon size={15} />}
          </button>
          {/* User info + role — hidden on mobile */}
          <div className="hidden sm:flex items-center gap-1.5">
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              {getNomeExibicao()}
            </span>
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full uppercase tracking-wider ${
              role === 'admin' ? 'bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'
              : role === 'supervisor' ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
              : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'
            }`}>
              {role === 'admin' ? 'Admin' : role === 'supervisor' ? 'Sup.' : 'Op.'}
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
            aria-label="Sair"
            title="Sair"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>

      {/* Admin nav links grid */}
      <div
        className={`grid ${cols} gap-2 transition-all duration-300 ease-in-out overflow-hidden ${
          hideNav
            ? 'opacity-0 pointer-events-none max-h-0 mb-0'
            : 'opacity-100 max-h-72 mb-6'
        }`}
      >
        {links.map(({ label, icon: Icon, pagina, path }) => {
          const ativo = paginaAtual === pagina
          return (
            <button
              key={pagina}
              onClick={() => navigate(path)}
              className={`rounded-xl py-2 px-1 text-xs font-semibold transition flex flex-col items-center gap-0.5 truncate ${
                ativo
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-primary-lighter dark:hover:bg-slate-700 hover:text-primary shadow-sm'
              }`}
            >
              <Icon size={16} />
              <span className="truncate">{label}</span>
            </button>
          )
        })}
      </div>

      {/* Mobile dropdown menu */}
      {hideNav && menuOpen && (
        <div ref={dropdownRef} className="absolute left-0 top-full z-50 w-full mt-2 animate-fade-in-up">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 p-3 flex flex-col gap-1">
            {(isAdmin || supervisorAdminLinks.length > 0) && (
              <>
                <div className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide px-2 py-1">
                  Administração
                </div>
                <div className="grid grid-cols-2 gap-1">
                  {adminLinksToShow.map(({ label, icon: Icon, pagina, path }) => {
                    const ativo = paginaAtual === pagina
                    return (
                      <button
                        key={pagina}
                        onClick={() => { navigate(path); setMenuOpen(false) }}
                        className={`rounded-xl py-2 px-2 text-xs font-semibold transition flex items-center gap-2 ${
                          ativo
                            ? 'bg-primary text-white shadow-sm'
                            : 'text-slate-600 dark:text-slate-300 hover:bg-primary-lighter dark:hover:bg-slate-700 hover:text-primary'
                        }`}
                      >
                        <Icon size={16} />
                        <span>{label}</span>
                      </button>
                    )
                  })}
                </div>
                <div className="border-t border-slate-200 dark:border-slate-700 my-1" />
              </>
            )}
            <div className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide px-2 py-1">
              Geral
            </div>
            <div className="grid grid-cols-2 gap-1">
              {COMMON_LINKS.map(({ label, icon: Icon, pagina, path }) => {
                const ativo = paginaAtual === pagina
                return (
                  <button
                    key={pagina}
                    onClick={() => { navigate(path); setMenuOpen(false) }}
                    className={`rounded-xl py-2 px-2 text-xs font-semibold transition flex items-center gap-2 ${
                      ativo
                        ? 'bg-primary text-white shadow-sm'
                        : 'text-slate-600 dark:text-slate-300 hover:bg-primary-lighter dark:hover:bg-slate-700 hover:text-primary'
                    }`}
                  >
                    <Icon size={16} />
                    <span>{label}</span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
