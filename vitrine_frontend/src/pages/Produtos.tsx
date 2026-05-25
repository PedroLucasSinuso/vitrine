import { useState } from 'react'
import { useTabelaProdutos } from '../hooks/useTabelaProdutos'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import ErrorBanner from '../components/ui/ErrorBanner'
import Skeleton from '../components/ui/Skeleton'
import { formatCurrency } from '../utils/formatters'

function margemVariant(margem: number): 'danger' | 'warning' | 'success' {
  if (margem < 10) return 'danger'
  if (margem < 20) return 'warning'
  return 'success'
}

function formatPercent(value: number): string {
  return `${value.toFixed(1).replace('.', ',')}%`
}

export default function Produtos() {
  const {
    items, total, loading, erro,
    search, setSearch,
    grupo, setGrupo,
    familia, setFamilia,
    sortBy, setSortBy,
    sortOrder, setSortOrder,
    page, setPage,
    pageSize, setPageSize,
    filtrosDisponiveis,
    totalPages,
    fetchData,
  } = useTabelaProdutos()

  const [searchInput, setSearchInput] = useState(search)

  function handleSort(col: string) {
    if (sortBy === col) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(col)
      setSortOrder('asc')
    }
  }

  function sortIndicator(col: string) {
    if (sortBy !== col) return null
    return sortOrder === 'asc' ? ' ▲' : ' ▼'
  }

  function renderPagination() {
    const pages: (number | 'ellipsis')[] = []
    const t = totalPages
    if (t <= 5) {
      for (let i = 0; i < t; i++) pages.push(i)
    } else {
      pages.push(0)
      let start = Math.max(1, page - 1)
      let end = Math.min(t - 2, page + 1)
      if (page <= 1) { start = 1; end = 3 }
      if (page >= t - 2) { start = t - 3; end = t - 2 }
      if (start > 1) pages.push('ellipsis')
      for (let i = start; i <= end; i++) pages.push(i)
      if (end < t - 2) pages.push('ellipsis')
      pages.push(t - 1)
    }
    return pages
  }

  const startRecord = total === 0 ? 0 : page * pageSize + 1
  const endRecord = Math.min((page + 1) * pageSize, total)

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-text-primary tracking-tight">Tabela de Preços</h1>
      </div>

      <Card variant="bordered">
        <div className="flex flex-col gap-4">
          {erro && (
            <ErrorBanner message={erro} onDismiss={fetchData} />
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
              <input
                type="text"
                placeholder="Buscar..."
                value={searchInput}
                onChange={(e) => { setSearchInput(e.target.value); setSearch(e.target.value) }}
                className="w-full pl-9 pr-3 py-2 border border-border-input bg-bg-input text-text-primary rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <select
              value={grupo}
              onChange={(e) => setGrupo(e.target.value)}
              className="border border-border-input bg-bg-input text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Todos os grupos</option>
              {filtrosDisponiveis.grupos.map(g => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
            <select
              value={familia}
              onChange={(e) => setFamilia(e.target.value)}
              className="border border-border-input bg-bg-input text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Todas as famílias</option>
              {filtrosDisponiveis.familias.map(f => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
          </div>

          {loading && items.length === 0 && (
            <div className="flex flex-col gap-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} variant="table-row" />
              ))}
            </div>
          )}

          {!loading && items.length === 0 && !erro && (
            <EmptyState title="Nenhum produto encontrado" />
          )}

          {items.length > 0 && (
            <div className="overflow-x-auto border border-border rounded-lg">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left bg-bg-card">
                    <th
                      className="py-3 px-3 text-xs text-text-muted font-medium whitespace-nowrap cursor-pointer hover:text-text-primary select-none"
                      onClick={() => handleSort('codigo_chamada')}
                    >
                      Código{sortIndicator('codigo_chamada')}
                    </th>
                    <th
                      className="py-3 px-3 text-xs text-text-muted font-medium whitespace-nowrap cursor-pointer hover:text-text-primary select-none"
                      onClick={() => handleSort('nome')}
                    >
                      Produto{sortIndicator('nome')}
                    </th>
                    <th
                      className="hidden md:table-cell py-3 px-3 text-xs text-text-muted font-medium whitespace-nowrap cursor-pointer hover:text-text-primary select-none"
                      onClick={() => handleSort('grupo')}
                    >
                      Grupo{sortIndicator('grupo')}
                    </th>
                    <th
                      className="hidden md:table-cell py-3 px-3 text-xs text-text-muted font-medium whitespace-nowrap cursor-pointer hover:text-text-primary select-none"
                      onClick={() => handleSort('familia')}
                    >
                      Família{sortIndicator('familia')}
                    </th>
                    <th
                      className="py-3 px-3 text-xs text-text-muted font-medium whitespace-nowrap text-right cursor-pointer hover:text-text-primary select-none"
                      onClick={() => handleSort('preco_custo')}
                    >
                      Custo{sortIndicator('preco_custo')}
                    </th>
                    <th
                      className="py-3 px-3 text-xs text-text-muted font-medium whitespace-nowrap text-right cursor-pointer hover:text-text-primary select-none"
                      onClick={() => handleSort('preco_venda')}
                    >
                      Venda{sortIndicator('preco_venda')}
                    </th>
                    <th className="py-3 px-3 text-xs text-text-muted font-medium whitespace-nowrap text-right">
                      Markup
                    </th>
                    <th className="py-3 px-3 text-xs text-text-muted font-medium whitespace-nowrap text-right">
                      Margem
                    </th>
                    <th
                      className="hidden md:table-cell py-3 px-3 text-xs text-text-muted font-medium whitespace-nowrap text-right cursor-pointer hover:text-text-primary select-none"
                      onClick={() => handleSort('estoque')}
                    >
                      Estoque{sortIndicator('estoque')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.codigo_chamada} className="border-b border-border last:border-0 hover:bg-bg-hover">
                      <td className="py-3 px-3 text-text-primary whitespace-nowrap">
                        <a
                          href={`/bi/sku?codigo=${item.codigo_chamada}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline font-medium"
                        >
                          {item.codigo_chamada}
                        </a>
                      </td>
                      <td className="py-3 px-3 text-text-primary truncate max-w-[200px]" title={item.nome}>
                        <a
                          href={`/bi/sku?codigo=${item.codigo_chamada}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline"
                        >
                          {item.nome}
                        </a>
                      </td>
                      <td className="hidden md:table-cell py-3 px-3 text-text-muted truncate max-w-[120px]" title={item.grupo}>
                        {item.grupo}
                      </td>
                      <td className="hidden md:table-cell py-3 px-3 text-text-muted truncate max-w-[120px]" title={item.familia}>
                        {item.familia}
                      </td>
                      <td className="py-3 px-3 text-text-primary text-right whitespace-nowrap font-mono">
                        {formatCurrency(item.preco_custo)}
                      </td>
                      <td className="py-3 px-3 text-text-primary text-right whitespace-nowrap font-mono font-semibold">
                        {formatCurrency(item.preco_venda)}
                      </td>
                      <td className="py-3 px-3 text-text-secondary text-right whitespace-nowrap">
                        {formatPercent(item.markup)}
                      </td>
                      <td className="py-3 px-3 text-right whitespace-nowrap">
                        <Badge variant={margemVariant(item.margem)}>
                          {formatPercent(item.margem)}
                        </Badge>
                      </td>
                      <td className="hidden md:table-cell py-3 px-3 text-text-primary text-right whitespace-nowrap">
                        {item.estoque}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {items.length > 0 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
              <p className="text-sm text-text-muted">
                Mostrando {startRecord}–{endRecord} de {total} resultados
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="p-2 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-bg-hover disabled:opacity-40 disabled:cursor-not-allowed transition"
                >
                  <ChevronLeft size={16} />
                </button>
                {renderPagination().map((p, i) =>
                  p === 'ellipsis' ? (
                    <span key={`e-${i}`} className="px-1 text-text-muted">...</span>
                  ) : (
                    <button
                      key={p}
                      onClick={() => setPage(p)}
                      className={`min-w-[32px] h-8 rounded-lg text-sm font-medium transition ${
                        page === p
                          ? 'bg-primary text-white'
                          : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'
                      }`}
                    >
                      {p + 1}
                    </button>
                  )
                )}
                <button
                  onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                  disabled={page >= totalPages - 1}
                  className="p-2 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-bg-hover disabled:opacity-40 disabled:cursor-not-allowed transition"
                >
                  <ChevronRight size={16} />
                </button>
                <select
                  value={pageSize}
                  onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0) }}
                  className="ml-2 border border-border-input bg-bg-input text-text-primary rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value={25}>25 / página</option>
                  <option value={50}>50 / página</option>
                  <option value={100}>100 / página</option>
                </select>
              </div>
            </div>
          )}

          {erro && !loading && items.length > 0 && (
            <button
              onClick={fetchData}
              className="text-sm text-primary hover:underline self-start"
            >
              Tentar novamente
            </button>
          )}
        </div>
      </Card>
    </div>
  )
}
