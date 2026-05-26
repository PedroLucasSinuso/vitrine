import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { LayoutDashboard, Search, Package, Settings, ShieldAlert } from 'lucide-react'
import type { Role } from '../../types'

interface MobileTab {
  label: string
  path: string
  icon: React.ReactNode
  roles: Role[]
}

const tabs: MobileTab[] = [
  { label: 'Resumo',   path: '/bi', icon: <LayoutDashboard size={22} />, roles: ['supervisor', 'admin'] },
  { label: 'Busca',    path: '/busca',                    icon: <Search size={22} />,          roles: ['operador', 'supervisor', 'admin'] },
  { label: 'Produtos', path: '/produtos',                 icon: <Package size={22} />,         roles: ['supervisor', 'admin'] },
  { label: 'Admin',    path: '/admin',                    icon: <ShieldAlert size={22} />,     roles: ['admin'] },
  { label: 'Config',   path: '/admin/configuracoes',      icon: <Settings size={22} />,        roles: ['admin'] },
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

      {/* Tabs */}
      <div className="relative flex items-center justify-around w-full max-w-lg mx-auto">
        {visibleTabs.map((tab) => {
          const active = isActive(tab.path)
          return (
            <button
              key={tab.path}
              onClick={() => navigate(tab.path)}
              className={`flex flex-col items-center justify-center gap-0.5 rounded-lg transition-all duration-fast min-w-[56px] py-1
                ${active
                  ? 'text-primary scale-110'
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
