import type { PerfilEmpresa, Role } from '../types'

export function paginaInicial(role: Role | null, perfil: PerfilEmpresa): string {
  const temBi = perfil.modulos.includes('dashboard')
  if (perfil.modo === 'upload') {
    if (role === 'operador') return perfil.modulos.includes('inventario') ? '/inventario' : '/importar'
    return temBi ? '/bi' : '/bi/equipe'
  }
  if (role === 'admin') return '/admin'
  if (role === 'supervisor') return '/bi'
  return '/inventario'
}

export const NOME_DO_EVENTO_PERFIL = 'vitrine:perfil-atualizar'

export function atualizarPerfil(): void {
  window.dispatchEvent(new Event(NOME_DO_EVENTO_PERFIL))
}
