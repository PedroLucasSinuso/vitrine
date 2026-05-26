import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useTheme } from '../../themes/useTheme'
import { getConfigsCache } from '../../stores/configStore'
import { buscarProdutosPorNome } from '../../api/produtos'
import type { ProdutoBasico } from '../../types'
import { Sun, Moon, LogOut, Search, ChevronRight } from 'lucide-react'
import NotificationCenter from '../NotificationCenter'

/**
 * AppHeader — cabeçalho minimalista
 *
 * Funciona como barra de topo para o conteúdo principal.
 * Em desktop a sidebar é a navegação principal, então o header
 * é minimal: breadcrumb (mobile), busca, ações do usuário.
 *
 * A busca de produtos implementa fuzzy search com dropdown:
 * - 300ms debounce em digitação com >= 2 caracteres
 * - Navegação via teclado (↑↓ + Enter) + mouse
 * - Enter sem seleção = navega com query literal
 */
export default function AppHeader() {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout, getRole, getNomeExibicao } = useAuth()
  const { theme, setTheme } = useTheme()
  const [marketName, setMarketName] = useState('')
  const [marketLogo, setMarketLogo] = useState('')
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<ProdutoBasico[]>([])
  const [showResults, setShowResults] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)
  const searchTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const searchContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

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

  // === Fuzzy search: debounced API call ===
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current)
    const q = query.trim()
    if (q.length < 2) {
      // Defer state updates to avoid setState-in-effect lint
      searchTimer.current = setTimeout(() => {
        setSearchResults([])
        setShowResults(false)
        setActiveIndex(-1)
      }, 0)
      return
    }
    searchTimer.current = setTimeout(async () => {
      try {
        const data = await buscarProdutosPorNome(q)
        setSearchResults(data)
        setShowResults(data.length > 0)
        setActiveIndex(-1)
      } catch {
        setSearchResults([])
        setShowResults(false)
      }
    }, 300)
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current) }
  }, [query])

  // === Click outside to close dropdown ===
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setShowResults(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  // === Navegar para o SKU de um produto ===
  const navigateToSku = useCallback((codigo: string) => {
    setQuery('')
    setSearchResults([])
    setShowResults(false)
    setActiveIndex(-1)
    navigate(`/bi/sku?codigo=${encodeURIComponent(codigo)}&force=1`)
  }, [navigate])

  // === Keyboard navigation ===
  function handleSearchKeyDown(e: React.KeyboardEvent) {
    const q = query.trim()
    if (!q) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((prev) => Math.min(prev + 1, searchResults.length - 1))
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((prev) => Math.max(prev - 1, 0))
      return
    }
    if (e.key === 'Escape') {
      setShowResults(false)
      inputRef.current?.blur()
      return
    }
    if (e.key === 'Enter') {
      // If there's an active selected item, use it
      if (activeIndex >= 0 && activeIndex < searchResults.length) {
        navigateToSku(searchResults[activeIndex].codigo_chamada)
      } else {
        // Fallback: navigate with raw query (treat as codigo)
        setQuery('')
        setSearchResults([])
        setShowResults(false)
        navigate(`/bi/sku?codigo=${encodeURIComponent(q)}&force=1`)
      }
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
          <div className="relative hidden sm:block" ref={searchContainerRef}>
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value)
                if (e.target.value.trim().length >= 2) {
                  // Show loading state — debounce handles results
                }
              }}
              onKeyDown={handleSearchKeyDown}
              onFocus={() => {
                if (searchResults.length > 0) setShowResults(true)
              }}
              placeholder="Buscar produto..."
              className="form-input-base w-40 lg:w-56 !pl-8 text-xs rounded-lg"
              aria-label="Buscar produto"
              autoComplete="off"
              spellCheck={false}
            />

            {/* Dropdown de resultados */}
            {showResults && searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-bg-card rounded-lg shadow-lg border border-border overflow-hidden z-40 max-h-72 overflow-y-auto">
                {searchResults.map((p, i) => (
                  <button
                    key={p.codigo_chamada}
                    onClick={() => navigateToSku(p.codigo_chamada)}
                    onMouseEnter={() => setActiveIndex(i)}
                    className={`
                      w-full text-left px-3 py-2 transition text-sm flex items-center justify-between gap-2
                      ${i === activeIndex ? 'bg-bg-hover' : 'hover:bg-bg-hover'}
                    `}
                  >
                    <span className="font-medium text-text-primary truncate">{p.nome}</span>
                    <span className="text-text-muted text-xs font-mono shrink-0">{p.codigo_chamada}</span>
                  </button>
                ))}
              </div>
            )}
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
