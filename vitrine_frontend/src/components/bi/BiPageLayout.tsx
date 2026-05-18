import type { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import AdminHeader from '../AdminHeader'
import BiSubNav from './BiSubNav'
import BiSideRail from './BiSideRail'

interface Props {
  titulo: string
  subtitulo?: string
  breadcrumb: { label: string; path?: string }[]
  maxWidth?: '3xl' | '4xl' | '5xl'
  hideSubNav?: boolean
  children: ReactNode
}

export default function BiPageLayout({ titulo, subtitulo, breadcrumb, maxWidth = '5xl', hideSubNav, children }: Props) {
  const location = useLocation()

  const containerWidth = maxWidth === '3xl'
    ? 'max-w-3xl xl:max-w-5xl 2xl:max-w-6xl'
    : maxWidth === '4xl'
    ? 'max-w-4xl xl:max-w-6xl 2xl:max-w-7xl'
    : 'max-w-5xl xl:max-w-7xl 2xl:max-w-[90rem]'

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6">
      <AdminHeader titulo={titulo} paginaAtual="bi" hideNav breadcrumb={breadcrumb} />
      {/* BiSubNav: mobile only — desktop uses BiSideRail */}
      {!hideSubNav && <div className="md:hidden w-full"><BiSubNav /></div>}
      {/* Page title */}
      <div className={`w-full ${containerWidth} mx-auto mb-4`}>
        <h1 className="text-2xl md:text-3xl font-bold text-slate-800 dark:text-slate-50 tracking-tight">{titulo}</h1>
        {subtitulo && <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">{subtitulo}</p>}
      </div>
      {/* Content area: centered with rail inside */}
      <div key={location.pathname} className="animate-page-in w-full">
        <div className={`w-full ${containerWidth} mx-auto flex gap-5`}>
          <div className="relative z-10">
            <BiSideRail />
          </div>
          <div className="flex-1 flex flex-col gap-5 min-w-0 relative z-0">{children}</div>
        </div>
      </div>
    </div>
  )
}
