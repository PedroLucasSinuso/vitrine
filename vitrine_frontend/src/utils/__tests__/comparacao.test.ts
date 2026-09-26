import { describe, it, expect } from 'vitest'
import { baseDeComparacao, variacaoSobreBase } from '../comparacao'

describe('base de comparação', () => {
  it('ausente ou zero não é base', () => {
    expect(baseDeComparacao(null)).toBeNull()
    expect(baseDeComparacao(undefined)).toBeNull()
    expect(baseDeComparacao(0)).toBeNull()
    expect(baseDeComparacao(150)).toBe(150)
  })

  it('variação só existe sobre uma base real', () => {
    expect(variacaoSobreBase(120, 100)).toBeCloseTo(20)
    expect(variacaoSobreBase(80, 100)).toBeCloseTo(-20)
    expect(variacaoSobreBase(100, 0)).toBeNull()
    expect(variacaoSobreBase(100, null)).toBeNull()
  })
})
