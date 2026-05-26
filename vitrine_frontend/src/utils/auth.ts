import type { Role } from '../types'

/**
 * Verifica se o role do usuário corresponde a um dos roles permitidos.
 * Centraliza as comparações de string de role (m1) para evitar que
 * mudanças futuras no enum quebrem comparações espalhadas pelo código.
 */
export function hasRole(userRole: string | null | undefined, allowed: Role[]): boolean {
  if (!userRole) return false
  return allowed.includes(userRole as Role)
}

/**
 * Cria prefixos de badge de role estilizados para UI.
 */
export function getRoleBadge(role: string | null | undefined): { label: string; className: string } {
  switch (role) {
    case 'admin':
      return {
        label: 'Admin',
        className: 'bg-purple-50 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
      }
    case 'supervisor':
      return {
        label: 'Sup.',
        className: 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
      }
    default:
      return {
        label: 'Op.',
        className: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
      }
  }
}
