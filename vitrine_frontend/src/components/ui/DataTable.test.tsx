import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DataTable from './DataTable'

interface Item { id: number; name: string }

const columns = [
  { header: 'ID', accessor: (row: Item) => row.id },
  { header: 'Nome', accessor: (row: Item) => row.name },
]

describe('DataTable', () => {
  it('renders headers and data', () => {
    const data = [{ id: 1, name: 'Item A' }]
    render(
      <DataTable
        columns={columns}
        data={data}
        keyExtractor={(row) => row.id}
      />
    )
    expect(screen.getByText('ID')).toBeInTheDocument()
    expect(screen.getByText('Item A')).toBeInTheDocument()
  })

  it('renders empty state', () => {
    render(
      <DataTable
        columns={columns}
        data={[]}
        keyExtractor={(row) => row.id}
        emptyState={<span>Vazio</span>}
      />
    )
    expect(screen.getByText('Vazio')).toBeInTheDocument()
  })

  it('renders footer', () => {
    render(
      <DataTable
        columns={columns}
        data={[]}
        keyExtractor={(row) => row.id}
        footer={<span>Total: 0</span>}
      />
    )
    expect(screen.getByText('Total: 0')).toBeInTheDocument()
  })
})
