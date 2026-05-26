import { useState, useCallback } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import AppHeader from './AppHeader'
import MobileNav from './MobileNav'

/**
 * AppLayout — layout principal do sistema
 *
 * Arquitetura:
 *   Desktop (lg+): Sidebar colapsável (240px ↔ 64px) | Header flutuante | Main
 *   Mobile  (<lg): Header compacto | Main | MobileNav bottom
 *
 * Premium features:
 *   • Sidebar colapsável com transição suave (300ms ease-out)
 *   • Header sem offset no desktop (sidebar é a navegação)
 *   • Main content com padding consistente usando spacing scale
 */
export default function AppLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    return localStorage.getItem('vitrine_sidebar_collapsed') === 'true'
  })

  const handleToggle = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const next = !prev
      localStorage.setItem('vitrine_sidebar_collapsed', String(next))
      return next
    })
  }, [])

  return (
    <div className="min-h-screen bg-bg-page text-text-primary antialiased selection:bg-primary/20">
      {/* Sidebar — desktop only */}
      <div className="hidden lg:block">
        <Sidebar collapsed={sidebarCollapsed} onToggle={handleToggle} />
      </div>

      {/* Main area — offset pela sidebar em desktop */}
      <div
        className="transition-all duration-300 ease-out lg:ml-[var(--sidebar-width)]"
        style={sidebarCollapsed ? { marginLeft: '64px' } : undefined}
      >
        {/* Header */}
        <AppHeader />

        {/* Page content */}
        <main className="min-h-[calc(100vh-var(--header-height))] pb-[var(--mobile-nav-height)] lg:pb-0">
          <div className="px-4 sm:px-6 py-4 sm:py-6 animate-page-in">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Mobile navigation */}
      <MobileNav />
    </div>
  )
}
