import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'

export function formatCurrency(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

/**
 * Format number with pt-BR locale, no decimals (e.g. "1.234")
 */
export function formatNumber(value: number): string {
  return value.toLocaleString('pt-BR', { maximumFractionDigits: 0 })
}

/**
 * Format ISO date string to "dd MMM yyyy" (e.g. "22 abr 2026")
 */
export function formatDate(iso: string | null): string {
  if (!iso) return '—'
  try {
    return format(parseISO(iso), "dd MMM yyyy", { locale: ptBR })
  } catch {
    return iso
  }
}

/**
 * Format ISO date string to "dd MMMM yyyy - EEEE" (e.g. "22 abril 2026 - Quarta-feira")
 */
export function formatDateWithWeekday(iso: string | null): string {
  if (!iso) return '—'
  try {
    return format(parseISO(iso), "dd MMMM yyyy - EEEE", { locale: ptBR })
  } catch {
    return iso
  }
}
