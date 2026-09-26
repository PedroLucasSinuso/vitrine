import { describe, it, expect } from 'vitest'
import { competenciaAnterior, competenciaAtual, linhasDeMeta, metasParaSalvar } from '../metas'

describe('metas', () => {
  it('competência atual e anterior, inclusive na virada do ano', () => {
    expect(competenciaAtual(new Date(2026, 8, 26))).toBe('2026-09')
    expect(competenciaAnterior('2026-09')).toBe('2026-08')
    expect(competenciaAnterior('2026-01')).toBe('2025-12')
  })

  it('inclui vendedores conhecidos sem meta e ordena por nome', () => {
    const linhas = linhasDeMeta(
      [{ vendedor: 'Mariana Souza', valor_meta: 10000, percentual_comissao: 2 }],
      ['mariana souza', 'Beatriz Lima'],
    )

    expect(linhas.map((l) => l.vendedor)).toEqual(['Beatriz Lima', 'Mariana Souza'])
    expect(linhas[0].valor_meta).toBe(0)
  })

  it('só salva linhas com meta positiva', () => {
    expect(metasParaSalvar([
      { vendedor: 'A', valor_meta: 0, percentual_comissao: 0 },
      { vendedor: 'B', valor_meta: 500, percentual_comissao: 1 },
    ])).toEqual([{ vendedor: 'B', valor_meta: 500, percentual_comissao: 1 }])
  })
})
