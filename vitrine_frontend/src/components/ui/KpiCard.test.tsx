import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import KpiCard from './KpiCard'
import { TrendingUp } from 'lucide-react'

describe('KpiCard', () => {
  it('renders label and value', () => {
    render(<KpiCard label="Receita" value="R$ 1.250" />)
    expect(screen.getByText('Receita')).toBeInTheDocument()
    expect(screen.getByText('R$ 1.250')).toBeInTheDocument()
  })

  it('renders trend up', () => {
    render(
      <KpiCard
        label="Margem"
        value="32.5%"
        trend={{ value: '+12.4%', direction: 'up' }}
      />
    )
    expect(screen.getByText('+12.4%')).toBeInTheDocument()
  })

  it('renders icon', () => {
    const { container } = render(
      <KpiCard label="Vendas" value="100" icon={<TrendingUp />} />
    )
    expect(container.querySelector('svg')).toBeInTheDocument()
  })
})
