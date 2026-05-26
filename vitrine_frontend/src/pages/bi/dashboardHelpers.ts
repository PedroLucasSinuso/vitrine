export interface VariacaoInfo {
  valor: number
  direcao: 'positivo' | 'negativo' | 'estavel'
}

export function variacaoInfo(pct: number | null): VariacaoInfo | null {
  if (pct === null) return null
  if (pct > 0) return { valor: pct, direcao: 'positivo' }
  if (pct < 0) return { valor: pct, direcao: 'negativo' }
  return { valor: 0, direcao: 'estavel' }
}
