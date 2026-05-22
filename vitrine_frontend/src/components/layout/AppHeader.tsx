import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useTheme } from '../../themes/useTheme'
import { getConfigsCache } from '../../stores/configStore'
import { Sun, Moon, LogOut, Search } from 'lucide-react'
import NotificationCenter from '../NotificationCenter'

export default function AppHeader() {
  const navigate = useNavigate()
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

  function handleSearchKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && query.trim()) {
      navigate(`/busca?q=${encodeURIComponent(query.trim())}`)
    }
  }

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  const roleBadge = role === 'admin' ? 'bg-purple-500/20 text-purple-400' :
    role === 'supervisor' ? 'bg-blue-500/20 text-blue-400' :
    'bg-slate-500/20 text-slate-400'

  return (
    <header className="sticky top-0 z-30 h-16 bg-bg-header backdrop-blur-md border-b border-border shrink-0 lg:ml-[240px]">
      <div className="h-full flex items-center gap-2 px-3 lg:px-4 max-w-screen-2xl mx-auto">

        {/* Block 1: Market Logo + Name */}
        <div className="flex items-center gap-2 min-w-0 shrink-0">
          {marketLogo ? (
            <img src={marketLogo} alt={marketName} className="h-7 w-auto rounded shrink-0" />
          ) : null}
          {marketName ? (
            <span className="text-sm font-semibold text-text-primary truncate max-w-[140px]">{marketName}</span>
          ) : null}
        </div>

        {/* Pipe divider */}
        <div className="w-px h-5 bg-border shrink-0" />

        {/* Block 2: Search (centered, flex-1) */}
        <div className="flex-1 flex justify-center min-w-0">
          <div className="relative w-full max-w-md">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="Buscar produto..."
              className="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-bg-input border border-border-input text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/40 transition"
              aria-label="Buscar produto"
            />
          </div>
        </div>

        {/* Pipe divider */}
        <div className="w-px h-5 bg-border shrink-0" />

        {/* Block 3: Actions */}
        <div className="flex items-center gap-0.5 shrink-0">
          <NotificationCenter />
          <button
            onClick={() => setTheme(theme === 'flagship' ? 'vitrine' : 'flagship')}
            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-hover transition"
            aria-label="Alternar tema"
            title={theme === 'flagship' ? 'Tema claro' : 'Tema escuro'}
          >
            {theme === 'flagship' ? <Sun size={14} /> : <Moon size={14} />}
          </button>
          <div className="hidden sm:flex items-center gap-1 ml-1">
            <span className="text-xs text-text-secondary font-medium truncate max-w-[90px]">
              {displayName}
            </span>
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full uppercase tracking-wider ${roleBadge}`}>
              {role === 'admin' ? 'Admin' : role === 'supervisor' ? 'Sup.' : 'Op.'}
            </span>
          </div>
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
