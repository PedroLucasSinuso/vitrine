import { useState } from 'react'
import { useTabelaProdutos } from '../hooks/useTabelaProdutos'
import { Search } from 'lucide-react'
import PageContainer from '../components/layout/PageContainer'
import PageSection from '../components/layout/PageSection'
import DataTable from '../components/ui/DataTable'
import Input from '../components/ui/Input'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'
import ErrorBanner from '../components/ui/ErrorBanner'
import type { ProdutoTabelaResponse } from '../types'
import { formatCurrency } from '../utils/formatters'

function margemVariant(margem: number): 'success' | 'warning' | 'danger' {
  if (margem < 10) return 'danger'
  if (margem < 20) return 'warning'
  return 'success'
}

function formatPercent(value: number): string {
  return `${value.toFixed(1).replace('.', ',')}%`
}

function codigoLink(codigo: string) {
  return `/bi/sku?codigo=${codigo}`
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

  const columns = [
    {
      key: 'codigo_chamada',
      label: 'Código',
      sortable: true,
      width: '100px',
      render: (item: ProdutoTabelaResponse) => (
        <a
          href={codigoLink(item.codigo_chamada)}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline font-medium"
        >
          {item.codigo_chamada}
        </a>
      ),
    },
    {
      key: 'nome',
      label: 'Produto',
      sortable: true,
      render: (item: ProdutoTabelaResponse) => (
        <a
          href={codigoLink(item.codigo_chamada)}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline"
        >
          <span className="truncate block max-w-[200px]" title={item.nome}>{item.nome}</span>
        </a>
      ),
    },
    {
      key: 'grupo',
      label: 'Grupo',
      sortable: true,
      hide: 'md' as const,
    },
    {
      key: 'familia',
      label: 'Família',
      sortable: true,
      hide: 'md' as const,
    },
    {
      key: 'preco_custo',
      label: 'Custo',
      sortable: true,
      align: 'right' as const,
      render: (item: ProdutoTabelaResponse) => (
        <span className="font-mono">{formatCurrency(item.preco_custo)}</span>
      ),
    },
    {
      key: 'preco_venda',
      label: 'Venda',
      sortable: true,
      align: 'right' as const,
      render: (item: ProdutoTabelaResponse) => (
        <span className="font-mono font-semibold">{formatCurrency(item.preco_venda)}</span>
      ),
    },
    {
      key: 'markup',
      label: 'Markup',
      align: 'right' as const,
      render: (item: ProdutoTabelaResponse) => (
        <span className="text-text-secondary">{formatPercent(item.markup)}</span>
      ),
    },
    {
      key: 'margem',
      label: 'Margem',
      align: 'right' as const,
      render: (item: ProdutoTabelaResponse) => (
        <Badge variant={margemVariant(item.margem)}>
          {formatPercent(item.margem)}
        </Badge>
      ),
    },
    {
      key: 'estoque',
      label: 'Estoque',
      sortable: true,
      align: 'right' as const,
      hide: 'md' as const,
    },
  ]

  return (
    <PageContainer maxWidth="xl">
      <PageSection
        title="Tabela de Preços"
        subtitle="Consulte preços, margens e estoque dos produtos"
      >
        {erro && (
          <ErrorBanner message={erro} onDismiss={fetchData} />
        )}

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Input
            icon={<Search size={14} />}
            placeholder="Buscar..."
            value={searchInput}
            onChange={(e) => { setSearchInput(e.target.value); setSearch(e.target.value) }}
          />
          <select
            value={grupo}
            onChange={(e) => setGrupo(e.target.value)}
            className="form-input-base"
          >
            <option value="">Todos os grupos</option>
            {filtrosDisponiveis.grupos.map(g => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
          <select
            value={familia}
            onChange={(e) => setFamilia(e.target.value)}
            className="form-input-base"
          >
            <option value="">Todas as famílias</option>
            {filtrosDisponiveis.familias.map(f => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>

        <DataTable
          data={items}
          columns={columns}
          rowKey={(item) => item.codigo_chamada}
          loading={loading}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSort={handleSort}
          page={page}
          pageSize={pageSize}
          total={total}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          empty={<EmptyState title="Nenhum produto encontrado" description="Tente ajustar os filtros da busca." />}
        />
      </PageSection>
    </PageContainer>
  )
}
