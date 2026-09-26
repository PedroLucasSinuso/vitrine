import type { DatasetResumo, IndicadoresLoja, IndicadoresVendedor, PeriodoBi, TipoDataset } from '../types'

export function formatarPercentual(valor: number, casas = 1): string {
  return `${(valor * 100).toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas })}%`
}

export function formatarDecimal(valor: number): string {
  return valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function formatarVariacao(valor: number | null): string {
  if (valor === null) return '—'
  const sinal = valor > 0 ? '+' : ''
  return `${sinal}${formatarPercentual(valor)}`
}

export function direcaoVariacao(valor: number | null): 'positivo' | 'negativo' | 'estavel' {
  if (valor === null || Math.abs(valor) < 0.005) return 'estavel'
  return valor > 0 ? 'positivo' : 'negativo'
}

export function taxaDeTroca(item: Pick<IndicadoresVendedor | IndicadoresLoja, 'trocas' | 'faturamento_bruto'>): number {
  return item.faturamento_bruto ? item.trocas / item.faturamento_bruto : 0
}

export function comparadoALoja(valor: number, referencia: number): number | null {
  return referencia ? valor / referencia - 1 : null
}

export const NOMES_TIPO_DATASET: Record<TipoDataset, string> = {
  vendas_vendedor_periodo: 'Vendas por vendedor no período',
  vendas_diarias: 'Vendas por dia',
  vendas_produto_periodo: 'Vendas por produto no período',
  contatos_vendedor: 'Contatos por vendedor',
  itens_venda: 'Itens vendidos',
}

export function formatarDataCurta(iso: string): string {
  const [ano, mes, dia] = iso.slice(0, 10).split('-')
  return `${dia}/${mes}/${ano}`
}

const TIPOS_DE_EQUIPE = new Set(['vendas_vendedor_periodo', 'vendas_diarias', 'itens_venda'])

export function periodosImportados(datasets: DatasetResumo[]): PeriodoBi[] {
  const vistos = new Set<string>()
  return datasets
    .filter((d) => TIPOS_DE_EQUIPE.has(d.tipo))
    .sort((a, b) => b.fim.localeCompare(a.fim))
    .map((d) => ({ data_inicio: d.inicio, data_fim: d.fim }))
    .filter((p) => {
      const chave = `${p.data_inicio}|${p.data_fim}`
      if (vistos.has(chave)) return false
      vistos.add(chave)
      return true
    })
}
