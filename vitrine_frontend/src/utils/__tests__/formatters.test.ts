import { describe, it, expect } from 'vitest'
import { formatEstoque } from '../formatters'

describe('formatEstoque', () => {
  it('usa vírgula como separador decimal, e não ponto', () => {
    // O ponto do float cru ("37.054") se lê como milhar em pt-BR — era
    // assim que 37 kg de alcatra apareciam como 37 mil na tabela de preços.
    expect(formatEstoque(37.054)).toBe('37,054')
  })

  it('não inventa casas decimais em produto vendido por unidade', () => {
    expect(formatEstoque(24)).toBe('24')
    expect(formatEstoque(0)).toBe('0')
  })

  it('agrupa milhar de verdade com ponto', () => {
    expect(formatEstoque(11514)).toBe('11.514')
  })
})
