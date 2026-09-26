export function baseDeComparacao(valor: number | null | undefined): number | null {
  return valor === null || valor === undefined || valor === 0 ? null : valor
}

export function variacaoSobreBase(atual: number, base: number | null | undefined): number | null {
  const referencia = baseDeComparacao(base)
  return referencia === null ? null : (atual / referencia - 1) * 100
}
