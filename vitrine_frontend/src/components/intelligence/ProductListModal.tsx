/** Modal com tabela de produtos de um insight + export CSV. */
import { useMemo } from 'react'
import { FileDown } from 'lucide-react'
import Modal from '../ui/Modal'
import Button from '../ui/Button'
import type { ProdutoInsight, InsightTipo } from '../../types/intelligence'
import { formatCurrency } from '../../utils/formatters'

interface Props {
  open: boolean
  onClose: () => void
  tipo: InsightTipo
  produtos: ProdutoInsight[]
}

type Coluna = { key: string; label: string; render: (p: ProdutoInsight) => string }

function getColunas(tipo: InsightTipo): Coluna[] {
  const base: Coluna[] = [
    { key: 'codigo', label: 'Código', render: p => p.codigo },
    { key: 'nome', label: 'Nome', render: p => p.nome },
  ]

  const extras: Record<InsightTipo, Coluna[]> = {
    encalhe: [
      { key: 'estoque', label: 'Estoque', render: p => String(p.estoque ?? '—') },
      { key: 'dias_parado', label: 'Dias parado', render: p => String(p.dias_parado ?? '—') },
      { key: 'valor_estimado', label: 'Valor estimado', render: p => p.valor_estimado != null ? formatCurrency(p.valor_estimado) : '—' },
    ],
    taxa_troca: [
      { key: 'taxa_troca', label: 'Taxa (%)', render: p => p.taxa_troca != null ? `${(p.taxa_troca * 100).toFixed(1)}%` : '—' },
      { key: 'qtd_trocas', label: 'Trocas', render: p => String(p.qtd_trocas ?? '—') },
      { key: 'qtd_vendas', label: 'Vendas', render: p => String(p.qtd_vendas ?? '—') },
    ],
    sazonalidade: [
      { key: 'crescimento_qtd', label: 'Crescimento (%)', render: p => p.crescimento_qtd != null ? `${(p.crescimento_qtd * 100).toFixed(0)}%` : '—' },
      { key: 'qtd_anterior', label: 'Qtd anterior', render: p => String(p.qtd_anterior ?? '—') },
      { key: 'qtd_atual', label: 'Qtd atual', render: p => String(p.qtd_atual ?? '—') },
      { key: 'valor_atual', label: 'Valor atual', render: p => p.valor_atual != null ? formatCurrency(p.valor_atual) : '—' },
    ],
    margem_erosao: [
      { key: 'margem_anterior', label: 'Margem ant. (%)', render: p => p.margem_anterior != null ? `${p.margem_anterior}%` : '—' },
      { key: 'margem_atual', label: 'Margem atual (%)', render: p => p.margem_atual != null ? `${p.margem_atual}%` : '—' },
      { key: 'variacao_pp', label: 'Variação (pp)', render: p => p.variacao_pp != null ? `${p.variacao_pp.toFixed(1)}` : '—' },
    ],
    oportunidade_b: [
      { key: 'margem_b', label: 'Margem B (%)', render: p => p.margem_b != null ? `${p.margem_b}%` : '—' },
      { key: 'margem_lider', label: 'Média A (%)', render: p => p.margem_lider != null ? `${p.margem_lider}%` : '—' },
      { key: 'upside_margem', label: 'Upside (%)', render: p => p.upside_margem != null ? `${p.upside_margem}%` : '—' },
      { key: 'potencial_ganho_mensal', label: 'Potencial/mês', render: p => p.potencial_ganho_mensal != null ? formatCurrency(p.potencial_ganho_mensal) : '—' },
    ],
    macro_contexto: [],
    outro: [],
  }

  return [...base, ...extras[tipo]]
}

function exportCSV(produtos: ProdutoInsight[], colunas: Coluna[], tipo: string) {
  const header = colunas.map(c => c.label).join(',')
  const rows = produtos.map(p =>
    colunas.map(c => `"${c.render(p).replace(/"/g, '""')}"`).join(',')
  )
  const csv = `\uFEFF${header}\n${rows.join('\n')}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `insight_${tipo}_${Date.now()}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

export default function ProductListModal({ open, onClose, tipo, produtos }: Props) {
  const colunas = useMemo(() => getColunas(tipo), [tipo])
  const tipoLabel = tipo.replace(/_/g, ' ')

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`${produtos.length} ${tipoLabel}`}
      size="xl"
      actions={
        <Button variant="secondary" size="sm" onClick={() => exportCSV(produtos, colunas, tipo)}>
          <FileDown size={14} className="mr-1" />
          Exportar CSV
        </Button>
      }
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="border-b border-border text-text-muted text-[11px] uppercase tracking-wider">
              {colunas.map(col => (
                <th key={col.key} className="py-2 pr-4 font-medium">{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {produtos.map((p, i) => (
              <tr key={p.codigo} className={i < produtos.length - 1 ? 'border-b border-border/50' : ''}>
                {colunas.map(col => (
                  <td key={col.key} className="py-2 pr-4 text-text-primary whitespace-nowrap">
                    {col.render(p)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {produtos.length === 0 && (
          <p className="text-sm text-text-muted py-4 text-center">Nenhum produto listado.</p>
        )}
      </div>
    </Modal>
  )
}
