import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useTheme } from '../../themes/useTheme'
import StatusPill from '../ui/StatusPill'
import type { Role } from '../../types'
import {
  LayoutDashboard, Search, Package, Users, Settings,
  Tags, ShieldAlert, HelpCircle, LogOut, Sun, Moon,
} from 'lucide-react'

interface NavItem {
  label: string
  path: string
  icon: React.ReactNode
  roles: Role[]
}

const navItems: NavItem[] = [
  { label: 'Dashboard',   path: '/bi',               icon: <LayoutDashboard size={18} />, roles: ['supervisor', 'admin'] },
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
  const { theme, setTheme } = useTheme()

  const role = getRole()
  const visibleItems = navItems.filter(item => role && item.roles.includes(role))

  const isActive = (path: string) => {
    if (path === '/bi') return location.pathname.startsWith('/bi')
    return location.pathname === path
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside className="hidden lg:flex lg:flex-col fixed left-0 top-0 h-full w-[240px] bg-bg-sidebar border-r border-border z-40">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 h-[64px] border-b border-border shrink-0">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-sm">
          V
        </div>
        <span className="font-display font-semibold text-base text-text-primary">Vitrine</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {visibleItems.map((item) => (
          <button
            key={item.path}
            onClick={() => navigate(item.path)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-fast text-left
              ${isActive(item.path)
                ? 'bg-bg-card text-primary shadow-sm'
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

        {/* Theme toggle */}
        <button
          onClick={() => setTheme(theme === 'flagship' ? 'vitrine' : 'flagship')}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-text-muted hover:text-text-primary hover:bg-bg-hover transition-all duration-fast"
        >
          {theme === 'flagship' ? <Sun size={18} /> : <Moon size={18} />}
          <span>{theme === 'flagship' ? 'Modo Claro' : 'Modo Escuro'}</span>
        </button>

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
