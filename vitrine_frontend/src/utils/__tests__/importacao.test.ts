import { describe, it, expect } from 'vitest'
import { largura, linhaDeCabecalhoProvavel, normalizar, sugerirColunas, sugerirTipo } from '../importacao'
import type { CampoDataset } from '../../types'

const CAMPOS_VENDEDOR: CampoDataset[] = [
  { campo: 'vendedor', rotulo: 'Vendedor', tipo: 'texto', obrigatorio: true },
  { campo: 'faturamento_bruto', rotulo: 'Faturamento bruto', tipo: 'numero', obrigatorio: true },
  { campo: 'atendimentos', rotulo: 'Atendimentos / tickets', tipo: 'inteiro', obrigatorio: true },
  { campo: 'pecas', rotulo: 'Peças', tipo: 'numero', obrigatorio: false },
  { campo: 'trocas', rotulo: 'Trocas', tipo: 'numero', obrigatorio: false },
]

describe('sugerirColunas', () => {
  it('reconhece o cabeçalho de um relatório de vendas por vendedor', () => {
    const cabecalho = ['Vendedor', 'Qtd Tickets', 'Qtd Peças', 'Valor (R$)', 'Trocas (R$)']

    expect(sugerirColunas(cabecalho, CAMPOS_VENDEDOR)).toEqual([
      { indice: 0, campo: 'vendedor' },
      { indice: 1, campo: 'atendimentos' },
      { indice: 2, campo: 'pecas' },
      { indice: 3, campo: 'faturamento_bruto' },
      { indice: 4, campo: 'trocas' },
    ])
  })

  it('não usa a mesma coluna para dois campos e ignora o que não reconhece', () => {
    const sugestao = sugerirColunas(['Colaborador', 'Observação'], CAMPOS_VENDEDOR)

    expect(sugestao).toEqual([{ indice: 0, campo: 'vendedor' }])
  })
})

describe('linhaDeCabecalhoProvavel', () => {
  it('pula título e período e acha a linha com vários textos', () => {
    const grade = [
      ['RELATÓRIO DE VENDAS'],
      ['Período: 01/09/2026 a 30/09/2026'],
      [],
      ['Vendedor', 'Tickets', 'Valor'],
      ['ANA', 10, 100],
    ]

    expect(linhaDeCabecalhoProvavel(grade)).toBe(3)
  })
})

describe('utilitários', () => {
  it('normaliza acentos e pontuação', () => {
    expect(normalizar('Qtd. Peças (R$)')).toBe('qtd pecas r')
  })

  it('largura é a maior linha', () => {
    expect(largura([[1], [1, 2, 3], []])).toBe(3)
  })
})

describe('sugerirTipo', () => {
  it.each([
    [['Vendedor', 'Qtd Tickets', 'Valor'], 'vendas_vendedor_periodo'],
    [['Data', 'Faturamento', 'Atendimentos'], 'vendas_diarias'],
    [['Data', 'Vendedor', 'Faturamento'], 'vendas_diarias'],
    [['Ticket', 'Data', 'Produto', 'Qtd', 'Valor'], 'itens_venda'],
    [['Produto', 'Quantidade', 'Receita'], 'vendas_produto_periodo'],
    [['vendedor', 'contatos', 'respostas'], 'contatos_vendedor'],
  ])('%j vira %s', (cabecalho, esperado) => {
    expect(sugerirTipo(cabecalho)).toBe(esperado)
  })
})

describe('sugerirColunas com o vocabulário de ERPs diferentes', () => {
  const mapa = (cabecalho: string[]) => Object.fromEntries(sugerirColunas(cabecalho, CAMPOS_VENDEDOR).map((c) => [c.campo, c.indice]))

  it.each([
    [['Cód', 'Nome do Vendedor', 'Cupons', 'Itens', 'Vlr Venda', 'Vlr Devolução'], { vendedor: 1, atendimentos: 2, pecas: 3, faturamento_bruto: 4, trocas: 5 }],
    [['Consultor', 'Nº Vendas', 'Qtde Itens', 'Total Vendido', 'Estornos'], { vendedor: 0, atendimentos: 1, pecas: 2, faturamento_bruto: 3, trocas: 4 }],
    [['Seller', 'Tickets', 'Units', 'Amount', 'Returns'], { vendedor: 0, atendimentos: 1, pecas: 2, faturamento_bruto: 3, trocas: 4 }],
    [['Vendedor', 'Tickets', 'Peças', 'Faturamento', 'Devoluções'], { vendedor: 0, atendimentos: 1, pecas: 2, faturamento_bruto: 3, trocas: 4 }],
    [['Vendedor', 'Qtd. Vendas', 'Qtd. Peças', 'Valor Bruto', 'Devolvido'], { vendedor: 0, atendimentos: 1, pecas: 2, faturamento_bruto: 3, trocas: 4 }],
  ])('%j', (cabecalho, esperado) => {
    expect(mapa(cabecalho)).toEqual(esperado)
  })

  it('a coluna de devolução nunca vira faturamento', () => {
    expect(mapa(['Vendedor', 'Vlr Devolução', 'Vlr Venda']).faturamento_bruto).toBe(2)
  })
})
