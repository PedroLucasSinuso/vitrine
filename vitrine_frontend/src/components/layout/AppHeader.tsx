import { useState, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Search, RefreshCw, Loader2, Sun, Moon } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'
import { useTheme } from '../../themes/useTheme'
import { useToast } from '../../hooks/useToast'
import StatusPill from '../ui/StatusPill'
import { triggerSync } from '../../api/admin'

const pageTitles: Record<string, string> = {
  '/busca': 'Busca de Produtos',
  '/home': 'Início',
  '/home/operador': 'Painel do Operador',
  '/admin': 'Administração',
  '/inventario': 'Inventário',
  '/admin/etiquetas': 'Etiquetas',
  '/admin/inventario': 'Inventário',
  '/admin/usuarios': 'Usuários',
  '/admin/configuracoes': 'Configurações',
  '/bi': 'Dashboard BI',
  '/bi/receita': 'Receita',
  '/bi/curva-abc': 'Curva ABC',
  '/bi/ranking': 'Ranking',
  '/bi/trocas': 'Trocas',
  '/bi/perdas-consumo': 'Perdas & Consumo',
  '/bi/temporal': 'Análise Temporal',
  '/bi/sku': 'Análise por SKU',
}

function getPageTitle(pathname: string): string {
  // Exact match first
  if (pageTitles[pathname]) return pageTitles[pathname]
  // Prefix match for BI routes
  if (pathname.startsWith('/bi/')) return 'BI'
  if (pathname.startsWith('/admin/')) return 'Administração'
  return 'Vitrine'
}

export default function AppHeader() {
  const location = useLocation()
  const navigate = useNavigate()
  const { getNomeExibicao } = useAuth()
  const { theme, setTheme } = useTheme()
  const { toast } = useToast()
  const [syncing, setSyncing] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const syncAbort = useRef<AbortController | null>(null)

  const title = getPageTitle(location.pathname)
  const nomeExibicao = getNomeExibicao()

  const handleSync = async () => {
    if (syncing) return
    setSyncing(true)
    syncAbort.current = new AbortController()
    try {
      await triggerSync()
      toast({ type: 'success', message: 'Sincronização concluída com sucesso' })
    } catch {
      toast({ type: 'error', message: 'Erro ao sincronizar com o ERP' })
    } finally {
      setSyncing(false)
      syncAbort.current = null
    }
  }

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      navigate(`/busca?q=${encodeURIComponent(searchQuery.trim())}`)
      setSearchQuery('')
    }
  }

  return (
    <header className="sticky top-0 z-30 h-[64px] bg-bg-header backdrop-blur-md border-b border-border flex items-center justify-between px-4 lg:px-6 gap-4">
      {/* Left: Page title */}
      <h1 className="font-display font-semibold text-lg text-text-primary truncate min-w-0">
        {title}
      </h1>

      {/* Center: Search */}
      <div className="hidden sm:flex relative flex-1 max-w-md">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Buscar produtos..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleSearchKeyDown}
          className="w-full h-9 pl-9 pr-3 text-sm bg-bg-input border border-border-input rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:border-border-focus transition-colors duration-fast"
        />
      </div>

      {/* Right: Status + Sync + Theme + Avatar */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Connection Status */}
        <div className="hidden sm:block">
          <StatusPill status="online" label="Online" />
        </div>

        {/* Sync button */}
        <button
          onClick={handleSync}
          disabled={syncing}
          className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-hover transition-all duration-fast disabled:opacity-50"
          aria-label="Sincronizar com ERP"
          title="Sincronizar com ERP"
        >
          {syncing ? <Loader2 size={18} className="animate-spin" /> : <RefreshCw size={18} />}
        </button>

        {/* Theme toggle (mobile only — sidebar has it on desktop) */}
        <button
          onClick={() => setTheme(theme === 'flagship' ? 'vitrine' : 'flagship')}
          className="lg:hidden p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-hover transition-all duration-fast"
          aria-label="Alternar tema"
        >
          {theme === 'flagship' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Avatar / User */}
        <div className="flex items-center gap-2 pl-2 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white font-semibold text-sm shrink-0">
            {nomeExibicao.charAt(0).toUpperCase()}
          </div>
          <span className="hidden md:block text-sm text-text-primary font-medium max-w-[140px] truncate">
            {nomeExibicao}
          </span>
        </div>
      </div>
    </header>
  )
}
