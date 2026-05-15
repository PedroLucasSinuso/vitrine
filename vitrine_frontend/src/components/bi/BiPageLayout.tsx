import type { ReactNode } from 'react'
import AdminHeader from '../AdminHeader'
import BiSubNav from './BiSubNav'

interface Props {
  titulo: string
  breadcrumb: { label: string; path?: string }[]
  maxWidth?: '3xl' | '4xl' | '5xl'
  children: ReactNode
}

const WIDTHS = { '3xl': 'max-w-3xl', '4xl': 'max-w-4xl', '5xl': 'max-w-5xl' }

export default function BiPageLayout({ titulo, breadcrumb, maxWidth = '5xl', children }: Props) {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
      <AdminHeader titulo={titulo} paginaAtual="bi" hideNav breadcrumb={breadcrumb} />
      <BiSubNav />
      <div className={`w-full ${WIDTHS[maxWidth]} flex flex-col gap-5`}>{children}</div>
    </div>
  )
}
