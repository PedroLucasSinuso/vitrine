export interface CsvRow {
  codigo: string
  tipo: string
  quantidade: number
}

export function gerarCSV(rows: CsvRow[]): string {
  return rows.map(r => `${r.codigo};${r.tipo};${r.quantidade}`).join('\n')
}

export function baixarCSV(conteudo: string, prefixo: string): void {
  const bom = "\uFEFF"
  const blob = new Blob([bom + conteudo], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${prefixo}_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

export function baixarCSVdeArray(dados: object[], prefixo: string): void {
  if (dados.length === 0) return
  const cabecalhos = Object.keys(dados[0])
  const linhas = dados.map((linha) =>
    cabecalhos.map((h) => {
      const v = (linha as Record<string, unknown>)[h]
      return v == null ? '' : String(v)
    }).join(';')
  )
  const csv = [cabecalhos.join(';'), ...linhas].join('\n')
  baixarCSV(csv, prefixo)
}
