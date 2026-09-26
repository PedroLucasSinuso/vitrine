import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { DetalheVendedor } from '../../../types'

const fetchDetalheVendedor = vi.fn()

vi.mock('../../../api/equipe', () => ({
  fetchDetalheVendedor: (...a: unknown[]) => fetchDetalheVendedor(...a),
}))

import Vendedor from '../Vendedor'

const BASE: DetalheVendedor = {
  periodo: { inicio: '2026-09-01', fim: '2026-09-26' },
  periodo_anterior: { inicio: '2026-08-01', fim: '2026-08-31' },
  comparacao_parcial: true,
  indicadores: {
    vendedor: 'MARIANA SOUZA', sem_vendedor: false, faturamento_bruto: 26000, trocas: 800, faturamento_liquido: 25200,
    atendimentos: 72, pecas: 170, ticket_medio: 361.11, pa: 2.36, preco_medio_peca: 152.94, participacao: 0.21,
    variacao_liquido: null, variacao_ticket_medio: 0.05, variacao_pa: -0.02, novo: false,
    meta: null, atingimento: null, projecao: null, comissao_estimada: null, contatos: null, conversao: null,
  },
  loja: {
    faturamento_bruto: 120000, trocas: 4000, faturamento_liquido: 116000, atendimentos: 420,
    atendimentos_somados_por_vendedor: true, ticket_medio: 285, pa: 2.4, meta: null, atingimento: null, projecao: null,
  },
  comparacao_loja: { ticket_medio: 0.27, pa: -0.02, preco_medio_peca: null, taxa_troca: -0.1 },
  posicao: 1,
  total_vendedores: 7,
  serie_mensal: null,
  serie_diaria: null,
  mix: null,
  indisponivel: [{ indicador: 'serie_diaria', motivo: 'Os dados enviados não trazem vendas por dia.' }],
}

function renderizar() {
  return render(
    <MemoryRouter initialEntries={['/bi/equipe/vendedor?nome=MARIANA%20SOUZA&inicio=2026-09-01&fim=2026-09-26']}>
      <Vendedor />
    </MemoryRouter>,
  )
}

describe('página do vendedor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    fetchDetalheVendedor.mockResolvedValue(BASE)
  })

  it('mostra só os blocos que existem e explica a comparação parcial', async () => {
    renderizar()

    expect(await screen.findByText('1º de 7 no ranking do período')).toBeTruthy()
    expect(screen.getByText(/só ticket médio e PA/)).toBeTruthy()
    expect(screen.getByText('Comparado à média da loja')).toBeTruthy()
    expect(screen.queryByText('Meta do mês')).toBeNull()
    expect(screen.queryByText('Conversão de contatos')).toBeNull()
    expect(screen.queryByText('Evolução mensal')).toBeNull()
    expect(screen.queryByText('Evolução diária')).toBeNull()
    expect(screen.getByText(/para ampliar esta análise/i)).toBeTruthy()
  })

  it('com meta, conversão e evolução mostra os três blocos', async () => {
    fetchDetalheVendedor.mockResolvedValue({
      ...BASE,
      indicadores: { ...BASE.indicadores, meta: 30000, atingimento: 0.84, projecao: 29000, comissao_estimada: 504, contatos: 180, conversao: 0.4 },
      serie_mensal: [
        { competencia: '2026-08', inicio: '2026-08-01', fim: '2026-08-31', parcial: false, sem_dados: false, ausente: false, faturamento_liquido: 27000, atendimentos: 80, ticket_medio: 337, pa: 2.4, taxa_troca: 0.03, vendedores_ativos: null },
        { competencia: '2026-09', inicio: '2026-09-01', fim: '2026-09-26', parcial: true, sem_dados: false, ausente: false, faturamento_liquido: 25200, atendimentos: 72, ticket_medio: 361, pa: 2.36, taxa_troca: 0.03, vendedores_ativos: null },
      ],
      indisponivel: [],
    })

    renderizar()

    expect(await screen.findByText('Meta do mês')).toBeTruthy()
    expect(screen.getByText('Conversão de contatos')).toBeTruthy()
    expect(screen.getByText('Evolução mensal')).toBeTruthy()
    expect(screen.queryByText(/para ampliar esta análise/i)).toBeNull()
  })

  it('vendedor sem venda no período mostra a explicação, não uma tela quebrada', async () => {
    fetchDetalheVendedor.mockRejectedValue({ response: { status: 404 } })

    renderizar()

    await waitFor(() => expect(screen.getByText('Este vendedor não tem vendas no período escolhido.')).toBeTruthy())
  })
})
