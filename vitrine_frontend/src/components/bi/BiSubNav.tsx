import { useEffect, useState, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

interface Tab {
  label: string
  path: string
}

const TABS: Tab[] = [
  { label: 'Dashboard', path: '/bi' },
  { label: 'Receita', path: '/bi/receita' },
  { label: 'Ranking', path: '/bi/ranking' },
  { label: 'Curva ABC', path: '/bi/curva-abc' },
  { label: 'Trocas', path: '/bi/trocas' },
  { label: 'Perdas e Consumo', path: '/bi/perdas-consumo' },
  { label: 'Temporal', path: '/bi/temporal' },
  { label: 'SKU', path: '/bi/sku' },
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

  // Scroll active tab into view within the scroll container
  useEffect(() => {
    const activeIndex = TABS.findIndex((tab) => location.pathname === tab.path)
    const container = scrollRef.current
    if (!container || activeIndex < 0) return

    const activeEl = container.children[0]?.children[activeIndex] as HTMLElement
    if (!activeEl) return

    const targetScroll = activeEl.offsetLeft - container.offsetWidth / 2 + activeEl.offsetWidth / 2
    container.scrollTo({ left: targetScroll, behavior: 'smooth' })
  }, [location.pathname])

  return (
    <div
      className={`w-full mb-4 transition-all duration-300 ease-in-out ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'
      }`}
    >
      {/* Outer scroll container — block element, overflow triggers scroll */}
      <div
        ref={scrollRef}
        className="overflow-x-auto pb-2"
        style={{
          WebkitOverflowScrolling: 'touch',
          overscrollBehaviorX: 'contain',
          msOverflowStyle: 'none',
          scrollbarWidth: 'none',
        }}
      >
        {/* Inner wrapper — inline-flex sizes to content, forcing overflow */}
        <div style={{ display: 'inline-flex', gap: '8px', whiteSpace: 'nowrap' }}>
          {TABS.map((tab) => {
            const ativo = location.pathname === tab.path
            return (
              <button
                key={tab.path}
                onClick={() => navigate(tab.path)}
                style={{ whiteSpace: 'nowrap', flexShrink: 0 }}
                className={`rounded-xl py-2 px-3 text-xs font-semibold transition shadow-sm ${
                  ativo
                    ? 'bg-primary text-white'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                }`}
              >
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
