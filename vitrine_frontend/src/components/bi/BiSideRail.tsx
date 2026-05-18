import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, BarChart3, PieChart, RefreshCw, Percent, Clock, Search } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface RailTab {
  label: string
  icon: LucideIcon
  path: string
}

const RAIL_TABS: RailTab[] = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/bi' },
  { label: 'Receita', icon: TrendingUp, path: '/bi/receita' },
  { label: 'Ranking', icon: BarChart3, path: '/bi/ranking' },
  { label: 'Curva ABC', icon: PieChart, path: '/bi/curva-abc' },
  { label: 'Trocas', icon: RefreshCw, path: '/bi/trocas' },
  { label: 'Perdas e Consumo', icon: Percent, path: '/bi/perdas-consumo' },
  { label: 'Temporal', icon: Clock, path: '/bi/temporal' },
  { label: 'SKU', icon: Search, path: '/bi/sku' },
]

export default function BiSideRail() {
  const location = useLocation()

  return (
    <nav className="hidden md:flex flex-col gap-1 sticky top-6 shrink-0" aria-label="Navegação rápida BI">
      {RAIL_TABS.map(({ label, icon: Icon, path }) => {
        const pathname = location.pathname.replace(/\/$/, '')
        const ativo = pathname === path
        return (
          <div key={path} className="relative group">
            {/* Lateral indicator for active tab */}
            {ativo && (
              <div className="absolute -left-1.5 top-1/2 -translate-y-1/2 w-1 h-5 bg-primary rounded-r-full" />
            )}
            <Link
              to={path}
              title={label}
              className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
                ativo
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-slate-400 dark:text-slate-500 hover:bg-white dark:hover:bg-slate-800 hover:text-primary hover:shadow-sm'
              }`}
              aria-current={ativo ? 'page' : undefined}
            >
              <Icon size={18} />
            </Link>
            {/* Hover tooltip */}
            <span className="absolute left-full ml-2 top-1/2 -translate-y-1/2 px-2 py-1 bg-slate-900 dark:bg-slate-700 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-150 whitespace-nowrap pointer-events-none z-50 shadow-sm">
              {label}
            </span>
          </div>
        )
      })}
    </nav>
  )
}
