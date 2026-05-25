import { useEffect, useState, useRef, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, BarChart3, PieChart, RefreshCw, Percent, Clock, Search } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Tab {
  label: string
  icon: LucideIcon
  path: string
}

const TABS: Tab[] = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/bi' },
  { label: 'Consolidado', icon: LayoutDashboard, path: '/bi/dashboard-consolidado' },
  { label: 'Receita', icon: TrendingUp, path: '/bi/receita' },
  { label: 'Ranking', icon: BarChart3, path: '/bi/ranking' },
  { label: 'Curva ABC', icon: PieChart, path: '/bi/curva-abc' },
  { label: 'Trocas', icon: RefreshCw, path: '/bi/trocas' },
  { label: 'Perdas', icon: Percent, path: '/bi/perdas-consumo' },
  { label: 'Temporal', icon: Clock, path: '/bi/temporal' },
  { label: 'SKU', icon: Search, path: '/bi/sku' },
]

export default function BiSubNav() {
  const navigate = useNavigate()
  const location = useLocation()
  const [visible, setVisible] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 50)
    return () => clearTimeout(t)
  }, [])

  const activeIndex = TABS.findIndex((tab) => location.pathname === tab.path)

  const scrollActiveTab = useCallback(() => {
    const container = scrollRef.current
    if (!container || activeIndex < 0) return

    const children = container.children[0]?.children
    if (!children || !children[activeIndex]) return

    const activeEl = children[activeIndex] as HTMLElement
    const targetScroll = activeEl.offsetLeft - container.offsetWidth / 2 + activeEl.offsetWidth / 2
    container.scrollTo({ left: targetScroll, behavior: 'smooth' })
  }, [activeIndex])

  useEffect(() => { scrollActiveTab() }, [scrollActiveTab])

  useEffect(() => {
    const handleResize = () => requestAnimationFrame(scrollActiveTab)
    window.addEventListener('resize', handleResize)
    window.addEventListener('orientationchange', handleResize)
    return () => {
      window.removeEventListener('resize', handleResize)
      window.removeEventListener('orientationchange', handleResize)
    }
  }, [scrollActiveTab])

  return (
    <div
      className={`w-full transition-all duration-300 ease-in-out ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'
      }`}
    >
      <div
        ref={scrollRef}
        className="overflow-x-auto"
        style={{
          WebkitOverflowScrolling: 'touch',
          overscrollBehaviorX: 'contain',
          msOverflowStyle: 'none',
          scrollbarWidth: 'none',
        }}
      >
        <div className="inline-flex gap-1 p-1 rounded-xl bg-bg-card border border-border min-w-0">
          {TABS.map((tab, i) => {
            const ativo = activeIndex === i
            return (
              <button
                key={tab.path}
                onClick={() => navigate(tab.path)}
                className={`
                  relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                  transition-all duration-200 shrink-0
                  ${ativo
                    ? 'bg-primary text-white shadow-sm shadow-primary/20'
                    : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'
                  }
                `}
              >
                <tab.icon size={14} strokeWidth={ativo ? 2.5 : 1.5} />
                <span className="whitespace-nowrap">{tab.label}</span>
                {/* Active glow dot */}
                {ativo && (
                  <span className="absolute -bottom-[3px] left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-white" />
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
