import { describe, it, expect } from 'vitest'
import { comparadoALoja, direcaoVariacao, formatarDataCurta, formatarPercentual, formatarVariacao, taxaDeTroca } from '../equipe'

describe('formatação da equipe', () => {
  it('percentual em pt-BR', () => {
    expect(formatarPercentual(0.1234)).toBe('12,3%')
    expect(formatarPercentual(0.5, 0)).toBe('50%')
  })

  it('variação com sinal e traço quando não há comparação', () => {
    expect(formatarVariacao(0.2)).toBe('+20,0%')
    expect(formatarVariacao(-0.05)).toBe('-5,0%')
    expect(formatarVariacao(null)).toBe('—')
  })

  it('direção ignora variações desprezíveis', () => {
    expect(direcaoVariacao(0.001)).toBe('estavel')
    expect(direcaoVariacao(0.1)).toBe('positivo')
    expect(direcaoVariacao(-0.1)).toBe('negativo')
    expect(direcaoVariacao(null)).toBe('estavel')
  })

  it('taxa de troca e comparação com a loja', () => {
    expect(taxaDeTroca({ trocas: 50, faturamento_bruto: 1000 })).toBe(0.05)
    expect(taxaDeTroca({ trocas: 0, faturamento_bruto: 0 })).toBe(0)
    expect(comparadoALoja(120, 100)).toBeCloseTo(0.2)
    expect(comparadoALoja(1, 0)).toBeNull()
  })

  it('data curta a partir de ISO', () => {
    expect(formatarDataCurta('2026-09-01')).toBe('01/09/2026')
    expect(formatarDataCurta('2026-09-01T10:00:00Z')).toBe('01/09/2026')
  })
})

describe('periodosImportados', () => {
  it('mais recente primeiro, sem repetir e só tipos que alimentam a equipe', async () => {
    const { periodosImportados } = await import('../equipe')
    const base = { linhas: 1, nome_origem: 'x', criado_em: '2026-09-01' }

    const periodos = periodosImportados([
      { ...base, id: 1, tipo: 'vendas_vendedor_periodo', inicio: '2026-08-01', fim: '2026-08-31' },
      { ...base, id: 2, tipo: 'vendas_vendedor_periodo', inicio: '2026-09-01', fim: '2026-09-30' },
      { ...base, id: 3, tipo: 'vendas_vendedor_periodo', inicio: '2026-09-01', fim: '2026-09-30' },
      { ...base, id: 4, tipo: 'contatos_vendedor', inicio: '2026-10-01', fim: '2026-10-31' },
    ])

    expect(periodos).toEqual([
      { data_inicio: '2026-09-01', data_fim: '2026-09-30' },
      { data_inicio: '2026-08-01', data_fim: '2026-08-31' },
    ])
  })
})
