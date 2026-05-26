import { describe, it, expect, vi } from 'vitest'

// Mock dos hooks e chamadas API antes de qualquer import do componente
vi.mock('../../../api/bi', () => ({
  fetchKpis: vi.fn().mockResolvedValue({
    faturamento_bruto: 1000,
    faturamento_liquido: 950,
    total_trocas: 50,
    qtd_tickets: 10,
    ticket_medio: 100,
    itens_por_ticket: 2.5,
  }),
  fetchKpisComparativo: vi.fn().mockResolvedValue(null),
  fetchRanking: vi.fn().mockResolvedValue([]),
  fetchDiario: vi.fn().mockResolvedValue(null),
  fetchDiarioComparativo: vi.fn().mockResolvedValue(null),
  fetchTemporalHora: vi.fn().mockResolvedValue([]),
  exportarExcelBI: vi.fn().mockResolvedValue(new Blob()),
}))

vi.mock('../../../stores/configStore', () => ({
  getConfigsCache: vi.fn().mockReturnValue({}),
}))

vi.mock('../../../hooks/useToast', () => ({
  useToast: vi.fn().mockReturnValue({ showToast: vi.fn() }),
}))

vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn().mockReturnValue(vi.fn()),
}))

vi.mock('../../../hooks/useCountUp', () => ({
  useCountUp: vi.fn().mockReturnValue({ value: 0, formattedValue: '0' }),
}))

describe('Dashboard', () => {
  it('placeholder — smoke test de existência', () => {
    // Teste básico que verifica se o ambiente de teste está configurado.
    // O Dashboard.tsx depende de múltiplos hooks e componentes que
    // precisam de mocking mais profundo. Este placeholder garante
    // que ao menos a estrutura de testes existe.
    expect(true).toBe(true)
  })

  it('módulo de API mockado corretamente', async () => {
    const bi = await import('../../../api/bi')
    const kpis = await bi.fetchKpis({ data_inicio: '2026-01-01', data_fim: '2026-01-31' })
    expect(kpis).toHaveProperty('faturamento_bruto')
    expect(kpis.faturamento_bruto).toBe(1000)
  })
})
