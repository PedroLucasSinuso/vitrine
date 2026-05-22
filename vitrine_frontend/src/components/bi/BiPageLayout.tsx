import type { ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import BiSubNav from './BiSubNav'

interface Props {
  titulo: string
  subtitulo?: string
  breadcrumb?: { label: string; path?: string }[]
  children: ReactNode
}

export default function BiPageLayout({ titulo, subtitulo, breadcrumb, children }: Props) {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <div className="flex flex-col gap-5">
      {/* Mobile breadcrumb */}
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

      {/* Page title */}
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-text-primary tracking-tight">{titulo}</h1>
        {subtitulo && <p className="text-sm text-text-muted mt-0.5">{subtitulo}</p>}
      </div>

      {/* BI Sub-nav — horizontal tab bar for all screen sizes */}
      <BiSubNav />

      {/* Content */}
      <div key={location.pathname} className="animate-page-in flex flex-col gap-5">
        {children}
      </div>
    </div>
  )
}
