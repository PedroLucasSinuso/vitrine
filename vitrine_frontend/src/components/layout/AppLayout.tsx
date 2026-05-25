import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import AppHeader from './AppHeader'
import MobileNav from './MobileNav'

/**
 * AppLayout — layout principal do sistema
 * 
 * Sidebar (lg+) | Header (sticky) | Main content | MobileNav
 * Todas as dimensões usam os tokens do design system.
 */
export default function AppLayout() {
  return (
    <div className="min-h-screen bg-bg-page text-text-primary antialiased">
      <Sidebar />

      {/* Header — offset pela sidebar em desktop */}
      <AppHeader />

      {/* Main content */}
      <main className="lg:ml-[var(--sidebar-width)] pt-[var(--header-height)] pb-[var(--mobile-nav-height)] lg:pb-0 min-h-screen">
        <div className="px-4 sm:px-6 py-4 sm:py-6 animate-page-in">
          <Outlet />
        </div>
      </main>

      <MobileNav />
    </div>
  )
}
