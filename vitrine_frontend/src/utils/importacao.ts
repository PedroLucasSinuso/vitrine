import type { CampoDataset, Celula, ColunaMapeada, TipoDataset } from '../types'

export const TIPOS_POR_PERIODO: TipoDataset[] = ['vendas_vendedor_periodo', 'vendas_produto_periodo', 'contatos_vendedor']

const PALAVRAS_CHAVE: Record<string, string[]> = {
  vendedor: ['vendedor', 'vendedora', 'colaborador', 'atendente', 'consultor', 'seller', 'sales rep', 'representante', 'funcionario'],
  atendimentos: ['ticket', 'atendimento', 'cupom', 'cupons', 'venda qtd', 'qtd vendas', 'qtde vendas', 'n vendas', 'nr vendas', 'num vendas', 'transacoes', 'orders'],
  pecas: ['peca', 'pecas', 'itens', 'qtd itens', 'units', 'unidades', 'qty', 'quantity'],
  faturamento_bruto: ['valor', 'vlr', 'faturamento', 'total vendido', 'venda bruta', 'vendas r', 'amount', 'vendido', 'revenue', 'sales'],
  faturamento_liquido: ['liquido'],
  trocas: ['troca', 'devoluc', 'devolv', 'estorno', 'return', 'refund'],
  data: ['data', 'dia', 'emissao'],
  produto: ['produto', 'descricao', 'item'],
  codigo_produto: ['codigo', 'cod', 'sku', 'referencia'],
  quantidade: ['qtd', 'quantidade', 'qtde'],
  receita: ['receita', 'valor', 'total'],
  valor: ['valor', 'total'],
  documento: ['ticket', 'cupom', 'documento', 'nota', 'pedido'],
  operacao: ['tipo', 'operacao'],
  grupo: ['grupo', 'departamento', 'secao'],
  familia: ['familia', 'categoria', 'subgrupo'],
  tamanho: ['tamanho', 'tam'],
  cor: ['cor'],
  colecao: ['colecao', 'temporada'],
  custo: ['custo'],
  contatos: ['contato', 'mensagen', 'disparo'],
  respostas: ['resposta'],
  conversoes: ['conversao', 'conversoes', 'vendas geradas'],
}

const EXCLUIR: Record<string, string[]> = {
  faturamento_bruto: ['devol', 'troca', 'estorn', 'return', 'refund', 'liquid', 'custo', 'net'],
  faturamento_liquido: ['bruto', 'gross'],
  receita: ['devol', 'troca', 'estorn', 'custo'],
  valor: ['devol', 'troca', 'estorn', 'custo'],
}

export function normalizar(texto: Celula): string {
  return String(texto ?? '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function combina(cabecalho: string, palavra: string): boolean {
  return ` ${cabecalho} `.includes(` ${palavra}`)
}

export function sugerirColunas(cabecalho: Celula[], campos: CampoDataset[]): ColunaMapeada[] {
  const usados = new Set<number>()
  const sugestao: ColunaMapeada[] = []
  for (const campo of campos) {
    const palavras = PALAVRAS_CHAVE[campo.campo] ?? [normalizar(campo.rotulo)]
    const excluir = EXCLUIR[campo.campo] ?? []
    const indice = cabecalho.findIndex((celula, i) => {
      const texto = normalizar(celula)
      return !usados.has(i) && palavras.some((p) => combina(texto, p)) && !excluir.some((e) => texto.includes(e))
    })
    if (indice >= 0) {
      usados.add(indice)
      sugestao.push({ indice, campo: campo.campo })
    }
  }
  return sugestao.sort((a, b) => a.indice - b.indice)
}

export function linhaDeCabecalhoProvavel(grade: Celula[][]): number {
  const indice = grade.findIndex((linha) => linha.filter((c) => typeof c === 'string' && c.trim() && !/\d{2}\/\d{2}/.test(c)).length >= 2)
  return indice >= 0 ? indice : 0
}

export function largura(grade: Celula[][]): number {
  return grade.reduce((maior, linha) => Math.max(maior, linha.length), 0)
}

export function sugerirTipo(cabecalho: Celula[]): TipoDataset {
  const textos = cabecalho.map(normalizar)
  const tem = (chave: string) => textos.some((t) => (PALAVRAS_CHAVE[chave] ?? [chave]).some((p) => combina(t, p)))
  if (tem('contatos')) return 'contatos_vendedor'
  if (tem('documento') && tem('produto')) return 'itens_venda'
  if (tem('vendedor')) return tem('data') ? 'vendas_diarias' : 'vendas_vendedor_periodo'
  if (tem('data')) return 'vendas_diarias'
  if (tem('produto')) return 'vendas_produto_periodo'
  return 'vendas_vendedor_periodo'
}
