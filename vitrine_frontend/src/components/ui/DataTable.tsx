import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react'

export interface Column<T> {
  key: string
  label: string
  sortable?: boolean
  align?: 'left' | 'right' | 'center'
  hide?: 'sm' | 'md' | 'lg'
  width?: string
  render?: (item: T) => React.ReactNode
  cellClass?: string
}

interface Props<T> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  empty?: React.ReactNode
  error?: string | null
  onRetry?: () => void
  onRowClick?: (item: T) => void
  rowKey: (item: T) => string | number
  /** External sort control */
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (key: string) => void
  /** Pagination props */
  page?: number
  pageSize?: number
  total?: number
  onPageChange?: (page: number) => void
  onPageSizeChange?: (size: number) => void
  pageSizeOptions?: number[]
  className?: string
}

function SortIcon({ active, direction }: { active: boolean; direction: 'asc' | 'desc' }) {
  if (!active) return <ChevronUp size={12} className="text-text-muted/40 ml-1 shrink-0" />
  return direction === 'asc'
    ? <ChevronUp size={12} className="text-primary ml-1 shrink-0" />
    : <ChevronDown size={12} className="text-primary ml-1 shrink-0" />
}

const hideMap: Record<string, string> = {
  sm: 'hidden sm:table-cell',
  md: 'hidden md:table-cell',
  lg: 'hidden lg:table-cell',
}

export default function DataTable<T>({
  data, columns, loading, empty, error, onRetry,
  onRowClick, rowKey,
  sortBy, sortOrder, onSort,
  page, pageSize, total, onPageChange, onPageSizeChange,
  pageSizeOptions = [25, 50, 100],
  className = '',
}: Props<T>) {
  const totalPages = pageSize && total ? Math.max(1, Math.ceil(total / pageSize)) : 0

  function renderPagination() {
    if (!pageSize || total == null || !onPageChange) return null
    const currentPage = page ?? 0
    const startRecord = total === 0 ? 0 : currentPage * pageSize + 1
    const endRecord = Math.min((currentPage + 1) * pageSize, total)

    const pages: (number | 'ellipsis')[] = []
    const t = totalPages
    if (t <= 7) {
      for (let i = 0; i < t; i++) pages.push(i)
    } else {
      pages.push(0)
      let start = Math.max(1, currentPage - 1)
      let end = Math.min(t - 2, currentPage + 1)
      if (currentPage <= 1) { start = 1; end = 3 }
      if (currentPage >= t - 2) { start = t - 3; end = t - 2 }
      if (start > 1) pages.push('ellipsis')
      for (let i = start; i <= end; i++) pages.push(i)
      if (end < t - 2) pages.push('ellipsis')
      pages.push(t - 1)
    }

    return (
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3">
        <p className="text-sm text-text-muted">
          Mostrando {startRecord}–{endRecord} de {total} resultados
        </p>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(Math.max(0, currentPage - 1))}
            disabled={currentPage === 0}
            className="p-1.5 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-bg-hover disabled:opacity-40 disabled:cursor-not-allowed transition"
            aria-label="Página anterior"
          >
            <ChevronLeft size={15} />
          </button>

          {pages.map((p, i) =>
            p === 'ellipsis' ? (
              <span key={`e-${i}`} className="px-1 text-text-muted select-none text-sm">...</span>
            ) : (
              <button
                key={p}
                onClick={() => onPageChange(p)}
                className={`min-w-[32px] h-8 rounded-lg text-sm font-medium transition ${
                  currentPage === p
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'
                }`}
              >
                {p + 1}
              </button>
            )
          )}

          <button
            onClick={() => onPageChange(Math.min(totalPages - 1, currentPage + 1))}
            disabled={currentPage >= totalPages - 1}
            className="p-1.5 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-bg-hover disabled:opacity-40 disabled:cursor-not-allowed transition"
            aria-label="Próxima página"
          >
            <ChevronRight size={15} />
          </button>

          {onPageSizeChange && (
            <select
              value={pageSize}
              onChange={(e) => { onPageSizeChange(Number(e.target.value)); onPageChange?.(0) }}
              className="ml-1 border border-border-input bg-bg-input text-text-primary rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
              aria-label="Itens por página"
            >
              {pageSizeOptions.map(s => (
                <option key={s} value={s}>{s} / pág</option>
              ))}
            </select>
          )}
        </div>
      </div>
    )
  }

  // Sort indicator helper
  function sortIndicator(key: string) {
    if (sortBy !== key) return <SortIcon active={false} direction="asc" />
    return <SortIcon active direction={sortOrder === 'asc' ? 'asc' : 'desc'} />
  }

  if (loading && data.length === 0) {
    return (
      <div className={`card-base ${className}`}>
        <div className="flex flex-col gap-2 p-5">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-4 bg-bg-hover rounded animate-pulse" style={{ width: `${70 + Math.random() * 30}%` }} />
          ))}
        </div>
      </div>
    )
  }

  if (error && data.length === 0) {
    return (
      <div className={`card-base p-5 ${className}`}>
        <div className="flex flex-col items-center gap-3 py-6">
          <p className="text-sm text-danger">{error}</p>
          {onRetry && (
            <button onClick={onRetry} className="text-sm text-primary hover:underline font-medium">
              Tentar novamente
            </button>
          )}
        </div>
      </div>
    )
  }

  if (data.length === 0 && empty) {
    return <>{empty}</>
  }

  return (
    <div className={`card-base overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <table className="table-base">
          <thead>
            <tr className="border-b border-border">
              {columns.map((col) => {
                const hideClass = col.hide ? hideMap[col.hide] : ''
                const alignClass = col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
                return (
                  <th
                    key={col.key}
                    className={`table-header-cell ${alignClass} ${hideClass} ${col.sortable ? 'cursor-pointer hover:text-text-primary select-none' : ''} ${col.width ? '' : ''}`}
                    style={col.width ? { width: col.width } : undefined}
                    onClick={() => col.sortable && onSort?.(col.key)}
                  >
                    <span className="inline-flex items-center">
                      {col.label}
                      {col.sortable && sortIndicator(col.key)}
                    </span>
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {data.map((item) => (
              <tr
                key={rowKey(item)}
                className={`table-row ${onRowClick ? 'cursor-pointer' : ''}`}
                onClick={() => onRowClick?.(item)}
              >
                {columns.map((col) => {
                  const hideClass = col.hide ? hideMap[col.hide] : ''
                  const alignClass = col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
                  const value = (item as Record<string, unknown>)[col.key]
                  return (
                    <td
                      key={col.key}
                      className={`table-cell ${alignClass} ${hideClass} ${col.cellClass ?? ''}`}
                    >
                      {col.render ? col.render(item) : (value as React.ReactNode) ?? '—'}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {renderPagination()}
    </div>
  )
}
