import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatusPill from './StatusPill'

describe('StatusPill', () => {
  it('renders online status', () => {
    render(<StatusPill status="online" />)
    expect(screen.getByText('Online')).toBeInTheDocument()
  })

  it('renders offline status', () => {
    render(<StatusPill status="offline" />)
    expect(screen.getByText('Offline')).toBeInTheDocument()
  })

  it('accepts custom label', () => {
    render(<StatusPill status="online" label="Conectado" />)
    expect(screen.getByText('Conectado')).toBeInTheDocument()
  })
})
