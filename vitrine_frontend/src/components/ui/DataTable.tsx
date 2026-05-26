import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight, SearchX } from 'lucide-react'

export interface Column<T> {
  key: string
  label: string
  sortable?: boolean
  align?: 'left' | 'right' | 'center'
  hide?: 'sm' | 'md' | 'lg'
  width?: string
  render?: (item: T) => React.ReactNode
  cellClass?: string
  /** Força texto monoespaçado */
  mono?: boolean
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
  /** Pagination */
  page?: number
  pageSize?: number
  total?: number
  onPageChange?: (page: number) => void
  onPageSizeChange?: (size: number) => void
  pageSizeOptions?: number[]
  /** Premium features */
  density?: 'sm' | 'md' | 'lg'
  stickyHeader?: boolean
  maxHeight?: string
  rowClassName?: (item: T) => string
  /** Exibe numeração automática à esquerda */
  rowNumbers?: boolean
  className?: string
}

function SortIcon({ active, direction }: { active: boolean; direction: 'asc' | 'desc' }) {
  if (!active) {
    return (
      <span className="inline-flex flex-col ml-1.5 -space-y-1 opacity-30 group-hover:opacity-60 transition-opacity">
        <ChevronUp size={10} strokeWidth={2.5} />
        <ChevronDown size={10} strokeWidth={2.5} />
      </span>
    )
  }
  return direction === 'asc'
    ? <ChevronUp size={14} className="text-primary ml-1.5 shrink-0" strokeWidth={2.5} />
    : <ChevronDown size={14} className="text-primary ml-1.5 shrink-0" strokeWidth={2.5} />
}

const hideMap: Record<string, string> = {
  sm: 'hidden sm:table-cell',
  md: 'hidden md:table-cell',
  lg: 'hidden lg:table-cell',
}

const densityMap: Record<string, string> = {
  sm: 'table-density-sm',
  md: '',
  lg: 'table-density-lg',
}

export default function DataTable<T>({
  data, columns, loading, empty, error, onRetry,
  onRowClick, rowKey,
  sortBy, sortOrder, onSort,
  page, pageSize, total, onPageChange, onPageSizeChange,
  pageSizeOptions = [25, 50, 100],
  density = 'md',
  stickyHeader = false,
  maxHeight,
  rowClassName,
  rowNumbers = false,
  className = '',
}: Props<T>) {
  const totalPages = pageSize && total ? Math.max(1, Math.ceil(total / pageSize)) : 0
  const densityClass = densityMap[density] || ''

  /* ── Pagination ── */
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
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-4 py-3 border-t border-border">
        <p className="text-xs text-text-muted">
          Mostrando <span className="font-medium text-text-secondary">{startRecord}</span>
          {' — '}
          <span className="font-medium text-text-secondary">{endRecord}</span>
          {' de '}
          <span className="font-medium text-text-secondary">{total}</span> resultados
        </p>

        <div className="flex items-center gap-1.5">
          {/* Prev */}
          <button
            onClick={() => onPageChange(Math.max(0, currentPage - 1))}
            disabled={currentPage === 0}
            className="flex items-center justify-center w-8 h-8 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-bg-hover disabled:opacity-30 disabled:cursor-not-allowed transition"
            aria-label="Página anterior"
          >
            <ChevronLeft size={15} />
          </button>

          {/* Page numbers */}
          <div className="flex items-center gap-0.5">
            {pages.map((p, i) =>
              p === 'ellipsis' ? (
                <span key={`e-${i}`} className="px-1 text-text-muted select-none text-xs">⋯</span>
              ) : (
                <button
                  key={p}
                  onClick={() => onPageChange(p)}
                  className={`min-w-[32px] h-8 rounded-lg text-xs font-semibold transition ${
                    currentPage === p
                      ? 'bg-primary text-white shadow-sm'
                      : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'
                  }`}
                >
                  {p + 1}
                </button>
              )
            )}
          </div>

          {/* Next */}
          <button
            onClick={() => onPageChange(Math.min(totalPages - 1, currentPage + 1))}
            disabled={currentPage >= totalPages - 1}
            className="flex items-center justify-center w-8 h-8 rounded-lg border border-border text-text-muted hover:text-text-primary hover:bg-bg-hover disabled:opacity-30 disabled:cursor-not-allowed transition"
            aria-label="Próxima página"
          >
            <ChevronRight size={15} />
          </button>

          {/* Page size */}
          {onPageSizeChange && (
            <select
              value={pageSize}
              onChange={(e) => { onPageSizeChange(Number(e.target.value)); onPageChange?.(0) }}
              className="ml-2 form-input-base !w-auto px-2 py-1.5 text-xs"
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

  /* ── Sort indicator ── */
  function sortIndicator(key: string) {
    if (sortBy !== key) return <SortIcon active={false} direction="asc" />
    return <SortIcon active direction={sortOrder === 'asc' ? 'asc' : 'desc'} />
  }

  /* ── Loading skeleton ── */
  if (loading && data.length === 0) {
    return (
      <div className={`card-base overflow-hidden ${className}`}>
        <div className="flex flex-col">
          {/* Header skeleton */}
          <div className="flex gap-4 px-4 py-3 border-b border-border">
            {columns.map((col) => (
              <div
                key={col.key}
                className="h-3 bg-bg-hover rounded animate-pulse"
                style={{ width: col.width || `${60 + (col.key.charCodeAt(0) % 30)}%`, flex: col.width ? '0 0 auto' : 1 }}
              />
            ))}
          </div>
          {/* Row skeletons */}
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex gap-4 px-4 py-3 border-b border-border-light last:border-0">
              {columns.map((col) => (
                <div
                  key={col.key}
                  className="h-3.5 bg-bg-hover/60 rounded animate-pulse"
                  style={{
                    width: col.width || `${50 + Math.random() * 40}%`,
                    flex: col.width ? '0 0 auto' : 1,
                    animationDelay: `${i * 80}ms`,
                  }}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    )
  }

  /* ── Error state ── */
  if (error && data.length === 0) {
    return (
      <div className={`card-base p-5 ${className}`}>
        <div className="flex flex-col items-center gap-3 py-8">
          <div className="w-10 h-10 rounded-full bg-danger-light flex items-center justify-center">
            <SearchX size={18} className="text-danger" />
          </div>
          <p className="text-sm text-danger font-medium">{error}</p>
          {onRetry && (
            <button onClick={onRetry} className="text-sm text-primary hover:underline font-medium transition">
              Tentar novamente
            </button>
          )}
        </div>
      </div>
    )
  }

  /* ── Empty state ── */
  if (data.length === 0 && empty) {
    return <>{empty}</>
  }

  if (data.length === 0 && !empty) {
    return null
  }

  /* ── Table ── */
  const tableHeader = (
    <thead>
      <tr className="border-b border-border">
        {rowNumbers && (
          <th className="table-header-cell text-center w-10">#</th>
        )}
        {columns.map((col) => {
          const hideClass = col.hide ? hideMap[col.hide] : ''
          const alignClass = col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
          const sortableClass = col.sortable ? 'table-header-cell-sortable group' : ''
          return (
            <th
              key={col.key}
              className={`${col.sortable ? sortableClass : 'table-header-cell'} ${alignClass} ${hideClass}`}
              style={col.width ? { width: col.width } : undefined}
              onClick={() => col.sortable && onSort?.(col.key)}
              aria-sort={sortBy === col.key ? (sortOrder === 'asc' ? 'ascending' : 'descending') : undefined}
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
  )

  const tableRows = (
    <tbody>
      {data.map((item, idx) => {
        const clickable = onRowClick ? 'table-row-clickable' : 'table-row'
        const customClass = rowClassName ? rowClassName(item) : ''
        return (
          <tr
            key={rowKey(item)}
            className={`${clickable} ${customClass}`}
            onClick={() => onRowClick?.(item)}
            tabIndex={onRowClick ? 0 : undefined}
            onKeyDown={onRowClick ? (e) => { if (e.key === 'Enter') onRowClick(item) } : undefined}
          >
            {rowNumbers && (
              <td className="table-cell text-center text-text-muted text-xs w-10">
                {(page ?? 0) * (pageSize ?? 0) + idx + 1}
              </td>
            )}
            {columns.map((col) => {
              const hideClass = col.hide ? hideMap[col.hide] : ''
              const alignClass = col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
              const monoClass = col.mono ? 'font-mono tabular-nums' : ''
              const value = (item as Record<string, unknown>)[col.key]
              return (
                <td
                  key={col.key}
                  className={`table-cell ${alignClass} ${hideClass} ${monoClass} ${col.cellClass ?? ''}`}
                >
                  {col.render ? col.render(item) : (value as React.ReactNode) ?? '\u2014'}
                </td>
              )
            })}
          </tr>
        )
      })}
    </tbody>
  )

  const wrapperClass = stickyHeader ? 'table-sticky-wrapper' : 'overflow-x-auto'

  return (
    <div className={`card-base overflow-hidden ${densityClass} ${className}`}>
      <div
        className={wrapperClass}
        style={!stickyHeader && maxHeight ? { maxHeight } : stickyHeader && maxHeight ? { maxHeight } : undefined}
      >
        <table className="table-base">
          {tableHeader}
          {tableRows}
        </table>
      </div>
      {renderPagination()}
    </div>
  )
}
