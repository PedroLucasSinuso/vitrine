import { format, parseISO } from 'date-fns'
import { ptBR } from 'date-fns/locale'

// ═══════════════════════════════════════════════════════════════════════════
// Moeda — R$ com formato pt-BR (1.234,56)
// ═══════════════════════════════════════════════════════════════════════════

const _currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
})

export function formatCurrency(value: number): string {
  return _currencyFormatter.format(value)
}

/**
 * Formata número com separador pt-BR, sem decimais (ex: "1.234").
 */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(value)
}

// ═══════════════════════════════════════════════════════════════════════════
// Timezone — UTC-3 (America/Sao_Paulo)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Converte string ISO (UTC ou com offset) para Date ajustado ao fuso Brasil.
 * 
 * Regras:
 * - Se tem offset explícito (Z, +03:00, -03:00): parseISO respeita → só formata
 * - Se NÃO tem offset: backend armazenou como UTC (SQLite func.now()) →
 *   parseISO trataria como local, mas precisamos subtrair 3h (UTC→BRT)
 */
export function toBrasiliaDate(iso: string): Date {
  let d = parseISO(iso)

  // Detecta se a string TEM informação de timezone (na parte AFTER 'T')
  const timePart = iso.includes('T') ? iso.split('T')[1] : iso
  // Z, +03:00, -03:00 na parte da hora → tem offset
  const hasOffset = timePart.endsWith('Z') || timePart.includes('+') || timePart.includes('-')

  if (!hasOffset) {
    // Sem offset: backend armazenou como UTC → converter para BRT (UTC-3)
    d = new Date(d.getTime() - 3 * 60 * 60 * 1000)
  }
  return d
}

/**
 * Formata data ISO no fuso Brasil (UTC-3).
 * Input sem offset explícito é tratado como UTC.
 * Ex: "22 abr 2026, 14:30"
 */
export function formatDataBrasil(iso: string): string {
  try {
    const d = toBrasiliaDate(iso)
    return d.toLocaleString('pt-BR', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return iso
  }
}

/**
 * Formata data ISO para "22 abr 2026" (sem hora).
 */
export function formatDataCurta(iso: string): string {
  try {
    const d = toBrasiliaDate(iso)
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
  } catch {
    return iso
  }
}

/**
 * Formata data ISO para "22 abril 2026 - Quarta-feira".
 */
export function formatDataComDiaSemana(iso: string): string {
  try {
    const d = toBrasiliaDate(iso)
    return d.toLocaleDateString('pt-BR', {
      day: '2-digit', month: 'long', year: 'numeric', weekday: 'long',
    })
  } catch {
    return iso
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Legado — mantido para compatibilidade
// ═══════════════════════════════════════════════════════════════════════════

/** @deprecated Use formatDataBrasil ou formatDataCurta — esta função
 *  usa date-fns que não converte timezone automaticamente. */
export function formatDate(iso: string | null): string {
  if (!iso) return '—'
  try {
    return format(parseISO(iso), "dd MMM yyyy", { locale: ptBR })
  } catch {
    return iso
  }
}

/** @deprecated Use formatDataComDiaSemana. */
export function formatDateWithWeekday(iso: string | null): string {
  if (!iso) return '—'
  try {
    return format(parseISO(iso), "dd MMMM yyyy - EEEE", { locale: ptBR })
  } catch {
    return iso
  }
}
