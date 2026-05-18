import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, LayoutDashboard, TrendingUp, BarChart3, PieChart, RefreshCw, Percent, Clock, Search as SearchIcon, Command } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface RouteEntry {
  label: string
  path: string
  icon: LucideIcon
  keywords: string
}

const ROUTES: RouteEntry[] = [
  { label: 'Dashboard BI', path: '/bi', icon: LayoutDashboard, keywords: 'dashboard bi kpi faturamento vendas' },
  { label: 'Receita por Dimensão', path: '/bi/receita', icon: TrendingUp, keywords: 'receita grupo familia produto vendas' },
  { label: 'Ranking de Produtos', path: '/bi/ranking', icon: BarChart3, keywords: 'ranking top produtos mais vendidos' },
  { label: 'Curva ABC', path: '/bi/curva-abc', icon: PieChart, keywords: 'curva abc classificacao Pareto 80/20' },
  { label: 'Trocas', path: '/bi/trocas', icon: RefreshCw, keywords: 'trocas devolucao substituicao' },
  { label: 'Perdas e Consumo', path: '/bi/perdas-consumo', icon: Percent, keywords: 'perdas consumo interno quebra' },
  { label: 'Temporal', path: '/bi/temporal', icon: Clock, keywords: 'temporal hora dia semana distribuicao' },
  { label: 'Análise SKU', path: '/bi/sku', icon: SearchIcon, keywords: 'sku codigo produto ean plu detalhe' },
  { label: 'Busca de Produtos', path: '/busca', icon: Search, keywords: 'busca produto preco estoque codigo' },
  { label: 'Admin — Sync ETL', path: '/admin', icon: RefreshCw, keywords: 'sync etl administracao' },
]

/**
 * Word-level substring matching: every word in the query must appear
 * somewhere in the target text (case-insensitive).
 */
function wordSubstringMatch(text: string, query: string): boolean {
  const q = query.toLowerCase()
  const words = q.split(/\s+/).filter(Boolean)
  const lower = text.toLowerCase()
  return words.every((w) => lower.includes(w))
}

export default function CmdK() {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [selectedIdx, setSelectedIdx] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const openRef = useRef(false)

  // Keep ref in sync with open state (for keyboard listener)
  useEffect(() => {
    openRef.current = open
  }, [open])

  // Global keyboard listener — registered once, uses ref for current open state
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen((prev) => !prev)
        setQuery('')
      }
      if (e.key === 'Escape' && openRef.current) {
        setOpen(false)
        setQuery('')
      }
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [])

  // Focus input when opened
  useEffect(() => {
    if (!open) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setQuery('')
    setSelectedIdx(0)
    const t = setTimeout(() => inputRef.current?.focus(), 0)
    return () => clearTimeout(t)
  }, [open])

  // Reset selection index when query changes
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSelectedIdx(0)
  }, [query])

  const navigateTo = useCallback((path: string) => {
    setOpen(false)
    setQuery('')
    navigate(path)
  }, [navigate])

  const filtered = query.trim()
    ? ROUTES.filter((r) => wordSubstringMatch(`${r.label} ${r.keywords}`, query))
    : ROUTES

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIdx((prev) => Math.min(prev + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIdx((prev) => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter' && filtered[selectedIdx]) {
      navigateTo(filtered[selectedIdx].path)
    } else if (e.key === 'Escape') {
      setOpen(false)
      setQuery('')
    }
  }

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current || !open) return
    const el = listRef.current.children[selectedIdx] as HTMLElement
    if (el) el.scrollIntoView({ block: 'nearest' })
  }, [selectedIdx, open])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/50 animate-fade-in-up"
      onClick={(e) => { if (e.target === e.currentTarget) { setOpen(false); setQuery('') }}}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Buscar páginas"
        className="w-full max-w-lg bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden animate-scale-in"
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-200 dark:border-slate-700">
          <Search size={16} className="text-slate-400 shrink-0" aria-hidden="true" />
          <input
            ref={inputRef}
            aria-label="Buscar páginas"
            className="flex-1 bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none"
            placeholder="Buscar páginas..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <kbd className="hidden sm:inline-flex items-center gap-0.5 text-[10px] text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-700 px-1.5 py-0.5 rounded">
            <Command size={10} />K
          </kbd>
        </div>

        {/* Results */}
        {filtered.length === 0 ? (
          <div className="px-4 py-8 text-center text-sm text-slate-400 dark:text-slate-500">
            Nenhuma página encontrada para &ldquo;{query}&rdquo;
          </div>
        ) : (
          <div
            ref={listRef}
            role="listbox"
            aria-activedescendant={filtered[selectedIdx] ? `cmdk-item-${selectedIdx}` : undefined}
            className="max-h-80 overflow-y-auto p-2 flex flex-col gap-0.5"
          >
            {filtered.map((r, i) => {
              const Icon = r.icon
              const isSelected = i === selectedIdx
              return (
                <button
                  key={r.path}
                  id={`cmdk-item-${i}`}
                  role="option"
                  aria-selected={isSelected}
                  onClick={() => navigateTo(r.path)}
                  onMouseEnter={() => setSelectedIdx(i)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-left transition ${
                    isSelected
                      ? 'bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-light'
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50'
                  }`}
                >
                  <Icon size={16} className="shrink-0 opacity-60" aria-hidden="true" />
                  <span className="flex-1 truncate">{r.label}</span>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono truncate max-w-24">{r.path}</span>
                </button>
              )
            })}
          </div>
        )}

        {/* Footer hint */}
        <div className="flex items-center gap-3 px-4 py-2 border-t border-slate-200 dark:border-slate-700 text-[10px] text-slate-400 dark:text-slate-500">
          <span><kbd className="bg-slate-50 dark:bg-slate-700 px-1 rounded text-[10px]">↑↓</kbd> Navegar</span>
          <span><kbd className="bg-slate-50 dark:bg-slate-700 px-1 rounded text-[10px]">↵</kbd> Abrir</span>
          <span><kbd className="bg-slate-50 dark:bg-slate-700 px-1 rounded text-[10px]">Esc</kbd> Fechar</span>
        </div>
      </div>
    </div>
  )
}
