import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DataTable from './DataTable'

interface Item { id: number; name: string }

const columns = [
  { key: 'id', label: 'ID', render: (row: Item) => row.id },
  { key: 'name', label: 'Nome', render: (row: Item) => row.name },
]

describe('DataTable', () => {
  it('renders headers and data', () => {
    const data = [{ id: 1, name: 'Item A' }]
    render(
      <DataTable
        columns={columns}
        data={data}
        rowKey={(row) => row.id}
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
        rowKey={(row) => row.id}
        empty={<span>Vazio</span>}
      />
    )
    expect(screen.getByText('Vazio')).toBeInTheDocument()
  })
})
