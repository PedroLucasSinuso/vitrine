import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Card from './Card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Conteúdo</Card>)
    expect(screen.getByText('Conteúdo')).toBeInTheDocument()
  })

  it('renders as button when onClick provided', () => {
    render(<Card onClick={() => {}}>Botão</Card>)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('applies variant classes', () => {
    const { container } = render(<Card variant="danger">Erro</Card>)
    expect(container.firstChild).toHaveClass('bg-danger-light')
  })
})
