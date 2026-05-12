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
  const [indicator, setIndicator] = useState({ left: 0, width: 0 })
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 50)
    return () => clearTimeout(t)
  }, [])

  useEffect(() => {
    const activeIndex = TABS.findIndex((tab) => location.pathname === tab.path)
    const container = containerRef.current
    if (!container || activeIndex < 0) return
    const activeEl = container.children[activeIndex] as HTMLElement
    if (activeEl) {
      const cr = container.getBoundingClientRect()
      const er = activeEl.getBoundingClientRect()
      setIndicator({ left: er.left - cr.left, width: er.width })
    }
  }, [location.pathname])

  return (
    <div
      className={`w-full max-w-5xl mb-6 transition-all duration-300 ease-in-out ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-2'
      }`}
    >
      <div className="relative">
        <div
          className="absolute bottom-1 h-0.5 bg-white rounded-full transition-all duration-300 ease-in-out pointer-events-none"
          style={{ left: indicator.left, width: indicator.width }}
        />
        <div
          ref={containerRef}
          className="flex gap-2 overflow-x-auto pb-1 scrollbar-none"
        >
          {TABS.map((tab) => {
            const ativo = location.pathname === tab.path
            return (
              <button
                key={tab.path}
                onClick={() => navigate(tab.path)}
                className={`rounded-xl py-2 px-3 text-xs font-semibold transition whitespace-nowrap shrink-0 ${
                  ativo
                    ? 'bg-primary text-white shadow-sm'
                    : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-primary-lighter dark:hover:bg-gray-700 hover:text-primary shadow-sm'
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
