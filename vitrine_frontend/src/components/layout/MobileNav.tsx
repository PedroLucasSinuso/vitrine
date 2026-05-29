import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { ClipboardList, LayoutDashboard, Search, Package, Settings, ShieldAlert, Tags, Sparkles } from 'lucide-react'
import type { Role } from '../../types'

interface MobileTab {
  label: string
  path: string
  icon: React.ReactNode
  roles: Role[]
}

const intelligenceEnabled = import.meta.env.VITE_INTELLIGENCE_ENABLED === 'true'

const tabs: MobileTab[] = [
  // Left side
  { label: 'Busca',      path: '/busca',                   icon: <Search size={20} />,          roles: ['operador', 'supervisor', 'admin'] },
  { label: 'Produtos',   path: '/produtos',                icon: <Package size={20} />,         roles: ['supervisor', 'admin'] },
  { label: 'Inventário', path: '/inventario',              icon: <ClipboardList size={20} />,   roles: ['operador', 'supervisor', 'admin'] },
  // Center — destacado
  { label: 'Resumo',     path: '/bi',                      icon: <LayoutDashboard size={24} />, roles: ['supervisor', 'admin'] },
  // Intelligence (condicional, ao lado do Resumo)
  ...(intelligenceEnabled ? [{ label: 'Intel.', path: '/bi/intelligence', icon: <Sparkles size={20} />, roles: ['supervisor', 'admin'] as Role[] }] : []),
  // Right side
  { label: 'Etiquetas',  path: '/etiquetas',               icon: <Tags size={20} />,            roles: ['operador', 'supervisor', 'admin'] },
  { label: 'Admin',      path: '/admin',                   icon: <ShieldAlert size={20} />,     roles: ['admin'] },
  { label: 'Config',     path: '/admin/configuracoes',     icon: <Settings size={20} />,        roles: ['admin'] },
]

export default function MobileNav() {
  const location = useLocation()
  const navigate = useNavigate()
  const { getRole } = useAuth()

  const role = getRole()
  const visibleTabs = tabs.filter(tab => role && tab.roles.includes(role))

  const isActive = (path: string) => {
    if (path === '/bi') return location.pathname.startsWith('/bi')
    return location.pathname === path
  }

  if (visibleTabs.length === 0) return null

  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around px-2"
      style={{ height: 'var(--mobile-nav-height)' }}
    >
      {/* Frosted background */}
      <div className="absolute inset-0 bg-bg-sidebar/90 backdrop-blur-lg border-t border-border" />

      {/* Tabs — scroll horizontal no mobile */}
      <div className="relative flex items-center w-full max-w-lg mx-auto gap-1 sm:gap-2 overflow-x-auto scrollbar-none whitespace-nowrap px-2">
        {visibleTabs.map((tab) => {
          const active = isActive(tab.path)
          const isCenter = tab.label === 'Resumo'

          if (isCenter) {
            return (
              <button
                key={tab.path}
                onClick={() => navigate(tab.path)}
                className={`flex flex-col items-center justify-center gap-0.5 rounded-2xl transition-all duration-fast min-w-[64px] py-2 -mt-3 shadow-lg
                  ${active
                    ? 'bg-primary text-white scale-110 shadow-primary/30'
                    : 'bg-primary/10 text-primary hover:bg-primary/20'
                  }`}
                aria-label={tab.label}
                aria-current={active ? 'page' : undefined}
              >
                {tab.icon}
                <span className="text-[10px] font-semibold leading-none">{tab.label}</span>
              </button>
            )
          }

          return (
            <button
              key={tab.path}
              onClick={() => navigate(tab.path)}
              className={`flex flex-col items-center justify-center gap-0.5 rounded-lg transition-all duration-fast min-w-[52px] py-1
                ${active
                  ? 'text-primary'
                  : 'text-text-muted hover:text-text-secondary'
                }`}
              aria-label={tab.label}
              aria-current={active ? 'page' : undefined}
            >
              {tab.icon}
              <span className="text-[10px] font-medium leading-none">{tab.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
