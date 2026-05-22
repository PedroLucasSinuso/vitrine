import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import AppHeader from './AppHeader'
import MobileNav from './MobileNav'

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-bg-page text-text-primary">
      <Sidebar />
      <AppHeader />

      {/* Main content */}
      <main className="lg:ml-[240px] pt-[64px] pb-[64px] lg:pb-0">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
          <Outlet />
        </div>
      </main>

      <MobileNav />
    </div>
  )
}
