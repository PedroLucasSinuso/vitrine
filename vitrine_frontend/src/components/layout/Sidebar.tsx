import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import StatusPill from '../ui/StatusPill'
import Logo from '../ui/Logo'
import type { Role } from '../../types'
import {
  BarChart3, Search, Package, Users, Settings,
  Tags, ShieldAlert, HelpCircle, LogOut,
} from 'lucide-react'

interface NavItem {
  label: string
  path: string
  icon: React.ReactNode
  roles: Role[]
}

const navItems: NavItem[] = [
  { label: 'BI',         path: '/bi',               icon: <BarChart3 size={18} />,          roles: ['supervisor', 'admin'] },
  { label: 'Produtos',   path: '/produtos',         icon: <Package size={18} />,            roles: ['supervisor', 'admin'] },
  { label: 'Busca',       path: '/busca',            icon: <Search size={18} />,          roles: ['operador', 'supervisor', 'admin'] },
  { label: 'Inventário',  path: '/inventario',       icon: <Package size={18} />,         roles: ['operador', 'supervisor', 'admin'] },
  { label: 'Usuários',    path: '/admin/usuarios',   icon: <Users size={18} />,           roles: ['admin'] },
  { label: 'Configurações', path: '/admin/configuracoes', icon: <Settings size={18} />,   roles: ['admin'] },
  { label: 'Etiquetas',   path: '/admin/etiquetas',  icon: <Tags size={18} />,            roles: ['supervisor', 'admin'] },
  { label: 'Admin',       path: '/admin',             icon: <ShieldAlert size={18} />,     roles: ['admin'] },
]

export default function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { getRole, logout } = useAuth()
  const role = getRole()
  const visibleItems = navItems.filter(item => role && item.roles.includes(role))

  const isActive = (path: string) => {
    // Exact match for specific pages; prefix match only for the root /bi
    if (path === '/bi') return location.pathname === '/bi'
    return location.pathname === path
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside className="hidden lg:flex lg:flex-col fixed left-0 top-0 h-full w-[240px] bg-bg-sidebar border-r border-border z-40">
      {/* Logo */}
      <div className="flex items-center px-5 h-[64px] border-b border-border shrink-0">
        <Logo height={28} className="text-primary" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {visibleItems.map((item) => (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-fast text-left
              ${isActive(item.path)
                ? 'bg-primary-light text-primary font-semibold'
                : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'
              }`}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-4 border-t border-border space-y-2">
        {/* Status */}
        <div className="px-3 py-2">
          <StatusPill status="online" label="Conectado" />
        </div>

        {/* Support */}
        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-text-muted hover:text-text-primary hover:bg-bg-hover transition-all duration-fast">
          <HelpCircle size={18} />
          <span>Suporte</span>
        </button>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-danger hover:bg-danger-light transition-all duration-fast"
        >
          <LogOut size={18} />
          <span>Sair</span>
        </button>
      </div>
    </aside>
  )
}
