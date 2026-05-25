import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useTheme } from '../../themes/useTheme'
import { getConfigsCache } from '../../stores/configStore'
import { Sun, Moon, LogOut, Search, ChevronRight } from 'lucide-react'
import NotificationCenter from '../NotificationCenter'

/**
 * AppHeader — cabeçalho minimalista
 *
 * Funciona como barra de topo para o conteúdo principal.
 * Em desktop a sidebar é a navegação principal, então o header
 * é minimal: breadcrumb (mobile), busca, ações do usuário.
 */
export default function AppHeader() {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout, getRole, getNomeExibicao } = useAuth()
  const { theme, setTheme } = useTheme()
  const [marketName, setMarketName] = useState('')
  const [marketLogo, setMarketLogo] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    getConfigsCache().then((c) => {
      if (c.marketName) setMarketName(c.marketName)
      if (c.marketLogoUrl) setMarketLogo(c.marketLogoUrl)
    }).catch(() => {})
  }, [])

  const role = getRole()
  const displayName = getNomeExibicao()

  // Gera breadcrumb a partir da pathname
  const pathParts = location.pathname.split('/').filter(Boolean)

  function handleSearchKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && query.trim()) {
      navigate(`/busca?q=${encodeURIComponent(query.trim())}`)
    }
  }

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  const roleBadge = role === 'admin'
    ? 'bg-purple-500/15 text-purple-500 dark:text-purple-400'
    : role === 'supervisor'
    ? 'bg-blue-500/15 text-blue-500 dark:text-blue-400'
    : 'bg-slate-500/15 text-slate-500 dark:text-slate-400'

  return (
    <header className="sticky top-0 z-30 bg-bg-header backdrop-blur-md border-b border-border">
      <div className="h-14 flex items-center gap-3 px-3 sm:px-5">

        {/* Left: Breadcrumb (mobile) + Market name */}
        <div className="flex items-center gap-2 min-w-0">
          {/* Mobile hamburger is handled by MobileNav */}

          {/* Market logo/name — visible on desktop, hidden on mobile */}
          <div className="hidden sm:flex items-center gap-2 shrink-0">
            {marketLogo ? (
              <img src={marketLogo} alt={marketName} className="h-6 w-auto rounded shrink-0" />
            ) : null}
            {marketName ? (
              <span className="text-sm font-semibold text-text-primary truncate max-w-[160px]">{marketName}</span>
            ) : null}
            {(marketLogo || marketName) && (
              <span className="w-px h-4 bg-border shrink-0 mx-1" />
            )}
          </div>

          {/* Breadcrumb */}
          <nav className="flex items-center gap-1 text-xs text-text-muted min-w-0" aria-label="Breadcrumb">
            {pathParts.length === 0 ? (
              <span className="text-text-secondary font-medium">Início</span>
            ) : (
              pathParts.map((part, i) => {
                const isLast = i === pathParts.length - 1
                const label = part.charAt(0).toUpperCase() + part.slice(1).replace(/-/g, ' ')
                return (
                  <span key={part} className="flex items-center gap-1 min-w-0">
                    {i > 0 && <ChevronRight size={10} className="opacity-40 shrink-0" />}
                    <span className={`truncate ${isLast ? 'text-text-secondary font-medium' : ''}`}>
                      {label}
                    </span>
                  </span>
                )
              })
            )}
          </nav>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right: Search + Actions */}
        <div className="flex items-center gap-1.5 shrink-0">
          {/* Search */}
          <div className="relative hidden sm:block">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Buscar produto..."
              className="w-40 lg:w-56 pl-8 pr-2.5 py-1.5 text-xs rounded-lg bg-bg-input border border-border-input text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-primary/40 transition"
              aria-label="Buscar produto"
            />
          </div>

          <span className="w-px h-4 bg-border shrink-0 mx-0.5" />

          <NotificationCenter />

          {/* Theme toggle */}
          <button
            onClick={() => setTheme(theme === 'flagship' ? 'vitrine' : 'flagship')}
            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-hover transition"
            aria-label="Alternar tema"
            title={theme === 'flagship' ? 'Tema claro' : 'Tema escuro'}
          >
            {theme === 'flagship' ? <Sun size={14} /> : <Moon size={14} />}
          </button>

          {/* User info */}
          <div className="hidden sm:flex items-center gap-1.5 ml-1">
            <span className="text-xs font-medium text-text-muted">{displayName}</span>
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full uppercase tracking-wider ${roleBadge}`}>
              {role === 'admin' ? 'Admin' : role === 'supervisor' ? 'Sup.' : 'Op.'}
            </span>
          </div>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="p-1.5 rounded-lg text-text-muted hover:text-danger hover:bg-danger-light transition"
            aria-label="Sair"
            title="Sair"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </header>
  )
}
