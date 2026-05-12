import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getConfiguracoes } from '../api/admin'

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
  icon: string
  pagina: string
  path: string
}

const ADMIN_LINKS: Link[] = [
  { label: 'Sync', icon: '\u{1F504}', pagina: 'sync', path: '/admin' },
  { label: 'Etiquetas', icon: '\u{1F3F7}\uFE0F', pagina: 'etiquetas', path: '/admin/etiquetas' },
  { label: 'Inventário', icon: '\u{1F4CB}', pagina: 'inventario', path: '/admin/inventario' },
  { label: 'Usuários', icon: '\u{1F465}', pagina: 'usuarios', path: '/admin/usuarios' },
  { label: 'Configurações', icon: '\u2699\uFE0F', pagina: 'configuracoes', path: '/admin/configuracoes' },
]

const COMMON_LINKS: Link[] = [
  { label: 'Busca', icon: '\u{1F50D}', pagina: 'busca', path: '/busca' },
  { label: 'BI', icon: '\u{1F4CA}', pagina: 'bi', path: '/bi' },
]

export default function AdminHeader({ titulo, paginaAtual, breadcrumb, hideNav, onLogout }: Props) {
  const navigate = useNavigate()
  const { logout, getRole, getNomeExibicao, getExpiresInMs } = useAuth()
  const role = getRole()

  const [dark, setDark] = useState(() => localStorage.getItem('darkMode') === 'true')
  const [menuOpen, setMenuOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const logoUrl = localStorage.getItem('marketLogoUrl')
  const marketName = localStorage.getItem('marketName')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('darkMode', String(dark))
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
    getConfiguracoes()
      .then((data) => {
        const c = data.configuracoes
        if (c.market_name) localStorage.setItem('marketName', c.market_name)
        if (c.logo_url) localStorage.setItem('marketLogoUrl', c.logo_url)
      })
      .catch(() => {})
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
      {breadcrumb && breadcrumb.length > 0 && (
        <nav className="text-xs text-gray-400 dark:text-gray-500 mb-2 flex gap-1 flex-wrap">
          {breadcrumb.map((b, i) => (
            <span key={i}>
              {i > 0 && <span className="mx-1">/</span>}
              {b.path
                ? <button onClick={() => navigate(b.path!)} className="hover:text-primary dark:hover:text-primary-light transition">{b.label}</button>
                : <span className="text-gray-600 dark:text-gray-300">{b.label}</span>
              }
            </span>
          ))}
        </nav>
      )}
      <div className="flex justify-between items-center mb-4 gap-2">
        <div className="flex items-center gap-3 min-w-0">
          {hideNav && (
            <button
              onClick={() => setMenuOpen((prev) => !prev)}
              className="flex items-center gap-1 text-xs font-semibold text-primary dark:text-primary-light bg-white dark:bg-gray-800 rounded-xl px-3 py-2 shadow-sm hover:bg-primary-lighter dark:hover:bg-gray-700 transition whitespace-nowrap shrink-0"
              aria-label="Abrir navegação admin"
            >
              {'\u2190'} Admin
            </button>
          )}
          {logoUrl ? (
            <img src={logoUrl} alt={marketName ?? 'Logo'} className="h-8 w-auto rounded shrink-0" />
          ) : (
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-sm shrink-0">
              {logoFallback}
            </div>
          )}
          <h1 className="text-xl font-bold text-gray-800 dark:text-gray-100 truncate">{titulo}</h1>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {expiringBadge && (
            <span className="text-xs bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300 font-semibold px-2 py-1 rounded-full">
              Token expira em {expiringMin}min
            </span>
          )}
          <button
            onClick={() => setDark((prev) => !prev)}
            className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
            aria-label="Alternar tema"
            title={dark ? 'Modo claro' : 'Modo escuro'}
          >
            {dark ? '\u2600' : '\u263E'}
          </button>
          <span className="text-xs text-gray-400 dark:text-gray-500">
            {getNomeExibicao()}
          </span>
          <button onClick={handleLogout} className="text-sm text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition">
            Sair
          </button>
        </div>
      </div>
      <div
        className={`grid ${cols} gap-2 transition-all duration-300 ease-in-out overflow-hidden ${
          hideNav
            ? 'opacity-0 pointer-events-none max-h-0 mb-0'
            : 'opacity-100 max-h-56 mb-6'
        }`}
      >
        {links.map(({ label, icon, pagina, path }) => {
          const ativo = paginaAtual === pagina
          return (
            <button
              key={pagina}
              onClick={() => navigate(path)}
              className={`rounded-xl py-2 px-1 text-xs font-semibold transition flex flex-col items-center gap-0.5 truncate ${
                ativo
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-primary-lighter dark:hover:bg-gray-700 hover:text-primary shadow-sm'
              }`}
            >
              <span className="text-base leading-none">{icon}</span>
              <span className="truncate">{label}</span>
            </button>
          )
        })}
      </div>
      {hideNav && menuOpen && (
        <div ref={dropdownRef} className="absolute left-0 top-full z-50 w-full mt-2 animate-fade-in-up">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-3 flex flex-col gap-1">
            {(isAdmin || supervisorAdminLinks.length > 0) && (
              <>
                <div className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide px-2 py-1">
                  Administração
                </div>
                <div className="grid grid-cols-2 gap-1">
                  {adminLinksToShow.map(({ label, icon, pagina, path }) => {
                    const ativo = paginaAtual === pagina
                    return (
                      <button
                        key={pagina}
                        onClick={() => { navigate(path); setMenuOpen(false) }}
                        className={`rounded-xl py-2 px-2 text-xs font-semibold transition flex items-center gap-2 ${
                          ativo
                            ? 'bg-primary text-white shadow-sm'
                            : 'text-gray-600 dark:text-gray-300 hover:bg-primary-lighter dark:hover:bg-gray-700 hover:text-primary'
                        }`}
                      >
                        <span className="text-base">{icon}</span>
                        <span>{label}</span>
                      </button>
                    )
                  })}
                </div>
                <div className="border-t border-gray-100 dark:border-gray-700 my-1" />
              </>
            )}
            <div className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide px-2 py-1">
              Geral
            </div>
            <div className="grid grid-cols-2 gap-1">
              {COMMON_LINKS.map(({ label, icon, pagina, path }) => {
                const ativo = paginaAtual === pagina
                return (
                  <button
                    key={pagina}
                    onClick={() => { navigate(path); setMenuOpen(false) }}
                    className={`rounded-xl py-2 px-2 text-xs font-semibold transition flex items-center gap-2 ${
                      ativo
                        ? 'bg-primary text-white shadow-sm'
                        : 'text-gray-600 dark:text-gray-300 hover:bg-primary-lighter dark:hover:bg-gray-700 hover:text-primary'
                    }`}
                  >
                    <span className="text-base">{icon}</span>
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