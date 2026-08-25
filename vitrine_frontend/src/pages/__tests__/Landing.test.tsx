import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'

const navigate = vi.fn()
const entrarNaDemo = vi.fn()
const demoDisponivel = vi.fn()

vi.mock('react-router-dom', () => ({
  useNavigate: () => navigate,
}))

vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({ entrarNaDemo }),
}))

vi.mock('../../api/auth', () => ({
  demoDisponivel: () => demoDisponivel(),
}))

import Landing from '../Landing'

describe('Landing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    demoDisponivel.mockResolvedValue(true)
    entrarNaDemo.mockResolvedValue('admin')
  })

  it('leva o visitante direto ao BI ao abrir a demonstração', async () => {
    render(<Landing />)
    const botao = await screen.findByRole('button', { name: /ver demonstração/i })

    fireEvent.click(botao)

    await waitFor(() => {
      expect(entrarNaDemo).toHaveBeenCalled()
      expect(navigate).toHaveBeenCalledWith('/bi', { replace: true })
    })
  })

  it('esconde o botão quando o servidor não tem demonstração', async () => {
    // Numa instalação de cliente real não há tenant de demo — oferecer o
    // botão levaria o usuário a um 404.
    demoDisponivel.mockResolvedValue(false)

    render(<Landing />)

    await waitFor(() => expect(demoDisponivel).toHaveBeenCalled())
    expect(screen.queryByRole('button', { name: /ver demonstração/i })).toBeNull()
    expect(screen.getByRole('button', { name: /já tenho conta/i })).toBeTruthy()
  })

  it('avisa em vez de travar quando a entrada falha', async () => {
    entrarNaDemo.mockRejectedValue(new Error('backend fora'))

    render(<Landing />)
    fireEvent.click(await screen.findByRole('button', { name: /ver demonstração/i }))

    expect(await screen.findByRole('alert')).toBeTruthy()
    expect(navigate).not.toHaveBeenCalled()
  })

  it('oferece a tela de login para quem já é cliente', async () => {
    render(<Landing />)

    fireEvent.click(screen.getByRole('button', { name: /já tenho conta/i }))

    expect(navigate).toHaveBeenCalledWith('/login')
  })
})
