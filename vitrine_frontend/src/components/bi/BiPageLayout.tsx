import type { ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import BiSubNav from './BiSubNav'

interface Props {
  titulo: string
  subtitulo?: string
  breadcrumb?: { label: string; path?: string }[]
  hideSubNav?: boolean
  children: ReactNode
}

export default function BiPageLayout({ titulo, subtitulo, breadcrumb, hideSubNav, children }: Props) {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div className="flex flex-col gap-5 max-w-full">
      {/* Breadcrumb (mobile only — desktop uses AdminHeader breadcrumb) */}
      {breadcrumb && breadcrumb.length > 0 && (
        <nav className="text-xs text-text-muted flex items-center gap-0.5 flex-wrap md:hidden" aria-label="Breadcrumb">
          {breadcrumb.map((b, i) => (
            <span key={i} className="flex items-center gap-0.5">
              {i > 0 && <ChevronRight size={10} className="opacity-40" />}
              {b.path
                ? <button onClick={() => navigate(b.path!)} className="hover:text-primary transition font-medium">{b.label}</button>
                : <span className="text-text-secondary font-medium">{b.label}</span>
              }
            </span>
          ))}
        </nav>
      )}

      {/* Page title + subtitle */}
      <div className="page-section-header mb-0">
        <div>
          <h1 className="page-section-title">{titulo}</h1>
          {subtitulo && <p className="page-section-subtitle">{subtitulo}</p>}
        </div>
      </div>

      {/* BI Sub-nav (oculto em páginas como Intelligence) */}
      {!hideSubNav && <BiSubNav />}

      {/* Content area */}
      <div key={location.pathname} className="animate-page-in flex flex-col gap-5">
        {children}
      </div>
    </div>
  )
}
