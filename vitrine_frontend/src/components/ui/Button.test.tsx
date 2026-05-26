import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Button from './Button'

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Salvar</Button>)
    expect(screen.getByText('Salvar')).toBeInTheDocument()
  })

  it('shows spinner when loading', () => {
    render(<Button loading>Salvar</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('applies variant classes', () => {
    const { container } = render(<Button variant="danger">Excluir</Button>)
    expect(container.firstChild).toHaveClass('bg-danger')
  })
})
