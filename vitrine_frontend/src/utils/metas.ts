import type { MetaVendedor } from '../types'

export function competenciaAtual(hoje = new Date()): string {
  return `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}`
}

export function competenciaAnterior(competencia: string): string {
  const [ano, mes] = competencia.split('-').map(Number)
  return mes === 1 ? `${ano - 1}-12` : `${ano}-${String(mes - 1).padStart(2, '0')}`
}

export function linhasDeMeta(metas: MetaVendedor[], conhecidos: string[]): MetaVendedor[] {
  const comMeta = new Set(metas.map((m) => m.vendedor.toUpperCase()))
  const semMeta = conhecidos
    .filter((nome) => !comMeta.has(nome.toUpperCase()))
    .map((vendedor) => ({ vendedor, valor_meta: 0, percentual_comissao: 0 }))
  return [...metas, ...semMeta].sort((a, b) => a.vendedor.localeCompare(b.vendedor, 'pt-BR'))
}

export function metasParaSalvar(linhas: MetaVendedor[]): MetaVendedor[] {
  return linhas.filter((l) => l.vendedor.trim() && l.valor_meta > 0)
}
