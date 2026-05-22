import type { ReactNode } from 'react'

export interface Column<T> {
  header: string
  accessor: (row: T) => ReactNode
  className?: string
  headerClassName?: string
}

interface Props<T> {
  columns: Column<T>[]
  data: T[]
  onRowClick?: (row: T) => void
  emptyState?: ReactNode
  footer?: ReactNode
  keyExtractor: (row: T) => string | number
  className?: string
}

export default function DataTable<T>({
  columns, data, onRowClick, emptyState, footer, keyExtractor, className = '',
}: Props<T>) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full text-left font-sans text-xs">
        <thead>
          <tr className="bg-bg-card border-b border-border">
            {columns.map((col, i) => (
              <th
                key={i}
                className={`px-6 py-3 font-mono text-[10px] text-text-muted uppercase tracking-widest font-semibold ${col.headerClassName ?? ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border/60">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-6 py-8 text-center text-text-muted">
                {emptyState ?? 'Nenhum registro encontrado.'}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={keyExtractor(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`transition-colors ${
                  onRowClick ? 'cursor-pointer hover:bg-bg-card-hover' : 'hover:bg-bg-card-hover'
                }`}
              >
                {columns.map((col, i) => (
                  <td key={i} className={`px-6 py-4 text-text-secondary ${col.className ?? ''}`}>
                    {col.accessor(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
        {footer && (
          <tfoot>
            <tr className="border-t border-border bg-bg-card">
              <td colSpan={columns.length} className="px-6 py-4 text-xs text-text-muted">
                {footer}
              </td>
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  )
}
