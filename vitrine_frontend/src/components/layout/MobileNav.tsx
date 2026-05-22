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
  { label: 'Dashboard',   path: '/bi',          icon: <LayoutDashboard size={22} />, roles: ['supervisor', 'admin'] },
  { label: 'Busca',       path: '/busca',       icon: <Search size={22} />,          roles: ['operador', 'supervisor', 'admin'] },
  { label: 'Inventário',  path: '/inventario',  icon: <Package size={22} />,         roles: ['operador', 'supervisor', 'admin'] },
  { label: 'Admin',       path: '/admin',                icon: <ShieldAlert size={22} />, roles: ['admin'] },
  { label: 'Config',      path: '/admin/configuracoes', icon: <Settings size={22} />,    roles: ['admin'] },
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

  // Se o usuário não tem nenhuma tab visível, não renderiza
  if (visibleTabs.length === 0) return null

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 h-[64px] bg-bg-sidebar border-t border-border z-50 flex items-center justify-around px-2 safe-area-bottom">
      {visibleTabs.map((tab) => (
        <button
          key={tab.path}
          onClick={() => navigate(tab.path)}
          className={`flex flex-col items-center justify-center gap-0.5 px-3 py-1 rounded-lg transition-all duration-fast min-w-[64px]
            ${isActive(tab.path)
              ? 'text-primary scale-110'
              : 'text-text-muted hover:text-text-secondary'
            }`}
          aria-label={tab.label}
        >
          {tab.icon}
          <span className="text-[10px] font-medium leading-none">{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}
