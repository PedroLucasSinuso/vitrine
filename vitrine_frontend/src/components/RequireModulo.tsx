import type { ReactNode } from 'react'
import NotFound from '../pages/NotFound'
import { usePerfilEmpresa } from '../stores/perfilEmpresaContexto'
import type { Modulo } from '../types'

export default function RequireModulo({ modulo, children }: { modulo: Modulo; children: ReactNode }) {
  const { carregado, temModulo } = usePerfilEmpresa()
  if (carregado && !temModulo(modulo)) return <NotFound />
  return <>{children}</>
}
