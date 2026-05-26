import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import Logo from '../ui/Logo'
import UserAvatar from '../ui/UserAvatar'
import type { Role } from '../../types'
import {
  BarChart3, Search, Package, ClipboardList, Users, Settings,
  Tags, ShieldAlert, HelpCircle, LogOut, ChevronLeft, PanelRightClose,
} from 'lucide-react'

interface NavItem {
  label: string
  path: string
  icon: React.ReactNode
  roles: Role[]
}

interface NavGroup {
  label: string
  items: NavItem[]
}

const navGroups: NavGroup[] = [
  {
    label: 'Análises',
    items: [
      { label: 'BI',        path: '/bi',             icon: <BarChart3 size={20} />,    roles: ['supervisor', 'admin'] },
      { label: 'Produtos',  path: '/produtos',       icon: <Package size={20} />,      roles: ['supervisor', 'admin'] },
    ],
  },
  {
    label: 'Operações',
    items: [
      { label: 'Busca',      path: '/busca',          icon: <Search size={20} />,       roles: ['operador', 'supervisor', 'admin'] },
      { label: 'Inventário', path: '/inventario',     icon: <ClipboardList size={20} />, roles: ['operador', 'supervisor', 'admin'] },
      { label: 'Etiquetas',  path: '/admin/etiquetas', icon: <Tags size={20} />,        roles: ['supervisor', 'admin'] },
    ],
  },
  {
    label: 'Sistema',
    items: [
      { label: 'Admin',      path: '/admin',          icon: <ShieldAlert size={20} />,  roles: ['admin'] },
      { label: 'Usuários',   path: '/admin/usuarios', icon: <Users size={20} />,        roles: ['admin'] },
      { label: 'Config.',    path: '/admin/configuracoes', icon: <Settings size={20} />, roles: ['admin'] },
    ],
  },
]

interface Props {
  collapsed: boolean
  onToggle: () => void
}

export default function Sidebar({ collapsed, onToggle }: Props) {
  const location = useLocation()
  const navigate = useNavigate()
  const { getRole, logout, getNomeExibicao } = useAuth()
  const role = getRole()
  const displayName = getNomeExibicao()

  const isActive = (path: string) => {
    if (path === '/bi') return location.pathname === '/bi' || location.pathname.startsWith('/bi/')
    if (path === '/admin') return location.pathname === '/admin' || (location.pathname.startsWith('/admin/') && !location.pathname.startsWith('/admin/usuarios') && !location.pathname.startsWith('/admin/configuracoes') && !location.pathname.startsWith('/admin/etiquetas'))
    if (path === '/admin/usuarios') return location.pathname.startsWith('/admin/usuario')
    if (path === '/admin/configuracoes') return location.pathname.startsWith('/admin/configuracoes')
    if (path === '/admin/etiquetas') return location.pathname.startsWith('/admin/etiquetas')
    return location.pathname === path
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  function navBtnClass(active: boolean, collapsed: boolean): string {
    const base = 'relative w-full flex items-center gap-3 rounded-lg text-sm font-medium transition-all duration-fast text-left'
    if (collapsed) return `${base} justify-center px-0 py-2.5 ${active ? 'text-primary font-semibold bg-bg-sidebar-item-active' : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'}`
    return `${base} px-3 py-2 ${active ? 'text-primary font-semibold bg-bg-sidebar-item-active' : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'}`
  }

  function bottomBtnClass(collapsed: boolean, danger = false): string {
    const base = 'w-full flex items-center gap-3 rounded-lg text-sm transition-all duration-fast'
    const color = danger
      ? 'text-danger hover:bg-danger-light'
      : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'
    if (collapsed) return `${base} justify-center px-0 py-2.5 ${color}`
    return `${base} px-3 py-2 ${color}`
  }

  return (
    <aside
      className={`fixed left-0 top-0 h-full z-40 bg-bg-sidebar border-r border-border flex flex-col transition-all duration-300 ease-out ${
        collapsed ? 'w-[64px]' : 'w-[var(--sidebar-width)]'
      }`}
    >
      {/* Logo + toggle */}
      <div className={`flex items-center h-[var(--header-height)] border-b border-border shrink-0 ${
        collapsed ? 'justify-center px-0' : 'justify-between px-5'
      }`}>
        {!collapsed && <Logo height={28} className="text-primary shrink-0" />}
        <button
          onClick={onToggle}
          className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-hover transition"
          aria-label={collapsed ? 'Expandir sidebar' : 'Recolher sidebar'}
          title={collapsed ? 'Expandir' : 'Recolher'}
        >
          {collapsed ? <PanelRightClose size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 space-y-5">
        {navGroups.map((group) => {
          const visibleItems = group.items.filter(item => role && item.roles.includes(role))
          if (visibleItems.length === 0) return null

          return (
            <div key={group.label}>
              {/* Group label */}
              {!collapsed && (
                <div className="px-5 mb-1.5">
                  <span className="text-[11px] font-semibold text-text-muted uppercase tracking-widest select-none">
                    {group.label}
                  </span>
                </div>
              )}

              {/* Items */}
              <div className="space-y-0.5 px-2">
                {visibleItems.map((item) => {
                  const active = isActive(item.path)
                  return (
                    <button
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      className={navBtnClass(active, collapsed)}
                      title={collapsed ? item.label : undefined}
                    >
                      {/* Active indicator bar */}
                      {active && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-primary rounded-r-full" />
                      )}

                      <span className="shrink-0">{item.icon}</span>
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </nav>

      {/* Bottom — User area */}
      <div className={`border-t border-border py-3 space-y-1 ${collapsed ? 'px-1' : 'px-3'}`}>
        {/* User profile */}
        {!collapsed ? (
          <div className="flex items-center gap-3 px-2 py-2 rounded-lg">
            <UserAvatar name={displayName} size="sm" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{displayName}</p>
              <span className="text-[11px] text-text-muted">Online</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center py-2">
            <UserAvatar name={displayName} size="sm" />
          </div>
        )}

        {/* Support */}
        <button className={bottomBtnClass(collapsed)} title={collapsed ? 'Ajuda' : undefined}>
          <HelpCircle size={18} className="shrink-0" />
          {!collapsed && <span>Ajuda</span>}
        </button>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className={bottomBtnClass(collapsed, true)}
          title={collapsed ? 'Sair' : undefined}
        >
          <LogOut size={18} className="shrink-0" />
          {!collapsed && <span>Sair</span>}
        </button>
      </div>
    </aside>
  )
}
