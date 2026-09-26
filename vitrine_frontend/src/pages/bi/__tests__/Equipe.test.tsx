import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { ResultadoEquipe } from '../../../types'

const fetchEquipe = vi.fn()
const fetchSerieVendedor = vi.fn()
const fetchMixVendedor = vi.fn()

vi.mock('../../../api/equipe', () => ({
  fetchEquipe: (...a: unknown[]) => fetchEquipe(...a),
  fetchSerieVendedor: (...a: unknown[]) => fetchSerieVendedor(...a),
  fetchMixVendedor: (...a: unknown[]) => fetchMixVendedor(...a),
}))

import Equipe from '../Equipe'

const RESULTADO: ResultadoEquipe = {
  periodo: { inicio: '2026-09-01', fim: '2026-09-30' },
  periodo_anterior: { inicio: '2026-08-02', fim: '2026-08-31' },
  competencia: '2026-09',
  loja: {
    faturamento_bruto: 25658.7, trocas: 509.9, faturamento_liquido: 25148.8,
    atendimentos: 155, atendimentos_somados_por_vendedor: true, ticket_medio: 165.54, pa: 2.52,
    meta: null, atingimento: null, projecao: null,
  },
  vendedores: [
    {
      vendedor: 'MARIANA SOUZA', sem_vendedor: false, faturamento_bruto: 8940.5, trocas: 320, faturamento_liquido: 8620.5,
      atendimentos: 42, pecas: 118, ticket_medio: 212.87, pa: 2.81, preco_medio_peca: 75.77, participacao: 0.3484,
      variacao_liquido: 0.12, variacao_ticket_medio: null, variacao_pa: null,
      meta: null, atingimento: null, projecao: null, comissao_estimada: null,
    },
    {
      vendedor: 'Sem vendedor', sem_vendedor: true, faturamento_bruto: 100, trocas: 0, faturamento_liquido: 100,
      atendimentos: 1, pecas: 1, ticket_medio: 100, pa: 1, preco_medio_peca: 100, participacao: 0.0039,
      variacao_liquido: null, variacao_ticket_medio: null, variacao_pa: null,
      meta: null, atingimento: null, projecao: null, comissao_estimada: null,
    },
  ],
  indisponivel: [
    { indicador: 'serie_diaria', motivo: 'Os dados enviados não trazem vendas por dia.' },
    { indicador: 'mix_categoria', motivo: 'Os dados enviados não trazem os itens vendidos.' },
  ],
}

function renderizar() {
  return render(<MemoryRouter><Equipe /></MemoryRouter>)
}

describe('Equipe', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fetchEquipe.mockResolvedValue(RESULTADO)
  })

  it('mostra KPIs da loja, ranking e a nota de atendimentos somados', async () => {
    renderizar()

    expect(await screen.findAllByText('MARIANA SOUZA')).not.toHaveLength(0)
    expect(screen.getByText('Sem vendedor')).toBeTruthy()
    expect(screen.getByText(/um atendimento com dois vendedores conta para os dois/i)).toBeTruthy()
    expect(screen.getByText('▲ +12,0%')).toBeTruthy()
  })

  it('detalhe do vendedor explica o que não dá para ver com os dados enviados', async () => {
    renderizar()
    const [linha] = await screen.findAllByText('MARIANA SOUZA')

    fireEvent.click(linha)

    const dialogo = await screen.findByRole('dialog')
    expect(within(dialogo).getByText('Os dados enviados não trazem vendas por dia.')).toBeTruthy()
    expect(within(dialogo).getByText('Os dados enviados não trazem os itens vendidos.')).toBeTruthy()
    expect(fetchSerieVendedor).not.toHaveBeenCalled()
    expect(fetchMixVendedor).not.toHaveBeenCalled()
  })

  it('com metas mostra atingimento, comissão e a projeção da loja', async () => {
    fetchEquipe.mockResolvedValue({
      ...RESULTADO,
      loja: { ...RESULTADO.loja, meta: 30000, atingimento: 0.8383, projecao: 29018 },
      vendedores: [{ ...RESULTADO.vendedores[0], meta: 10000, atingimento: 0.862, projecao: 9947, comissao_estimada: 172.41 }],
    })

    renderizar()

    expect(await screen.findByText(/Meta da loja: 84% de R\$\s?30\.000,00/)).toBeTruthy()
    expect(screen.getByText(/Projeção do mês/)).toBeTruthy()
    expect(screen.getByTitle(/86% de R\$\s?10\.000,00/)).toBeTruthy()
    expect(screen.getAllByText(/R\$\s?172,41/).length).toBeGreaterThan(0)
  })

  it('mostra estado vazio sem vendas', async () => {
    fetchEquipe.mockResolvedValue({ ...RESULTADO, vendedores: [] })

    renderizar()

    await waitFor(() => expect(screen.getByText('Nenhuma venda no período')).toBeTruthy())
  })

  it('mostra o erro da API', async () => {
    fetchEquipe.mockRejectedValue({ response: { data: { detail: 'Período máximo permitido é 180 dias' } } })

    renderizar()

    expect(await screen.findByText('Período máximo permitido é 180 dias')).toBeTruthy()
  })
})
