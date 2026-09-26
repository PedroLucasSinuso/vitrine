import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PerfilEmpresaProvider } from '../perfilEmpresa'
import { usePerfilEmpresa } from '../perfilEmpresaContexto'
import { limparCachePerfil } from '../../utils/perfilCache'

const getPerfilEmpresa = vi.fn()
let usuario: string | null = 'gerente'

vi.mock('../../api/empresa', () => ({ getPerfilEmpresa: () => getPerfilEmpresa() }))
vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: () => usuario !== null, getUsername: () => usuario }),
}))

function Sonda() {
  const { perfil, carregado, rotulo } = usePerfilEmpresa()
  return <p>{`${perfil.segmento}|${carregado}|${rotulo('grupo')}`}</p>
}

function renderizar() {
  return render(<MemoryRouter><PerfilEmpresaProvider><Sonda /></PerfilEmpresaProvider></MemoryRouter>)
}

const PERFIL_MODA = {
  nome: 'Loja', segmento: 'moda', modo: 'legado', modulos: ['dashboard'],
  rotulos: { grupo: 'Departamento', grupos: 'Departamentos', familia: 'Categoria', familias: 'Categorias', documento: 'Atendimento' },
}

describe('PerfilEmpresaProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    limparCachePerfil()
    usuario = 'gerente'
  })

  it('começa no perfil padrão e troca pelo da API', async () => {
    getPerfilEmpresa.mockResolvedValue(PERFIL_MODA)

    renderizar()

    expect(screen.getByText('supermercado|false|Grupo')).toBeTruthy()
    await waitFor(() => expect(screen.getByText('moda|true|Departamento')).toBeTruthy())
  })

  it('mantém o padrão quando a API falha', async () => {
    getPerfilEmpresa.mockRejectedValue(new Error('offline'))

    renderizar()

    await waitFor(() => expect(getPerfilEmpresa).toHaveBeenCalled())
    expect(screen.getByText('supermercado|false|Grupo')).toBeTruthy()
  })

  it('usa o cache do usuário enquanto a API não responde', async () => {
    getPerfilEmpresa.mockResolvedValue(PERFIL_MODA)
    const { unmount } = renderizar()
    await waitFor(() => expect(screen.getByText('moda|true|Departamento')).toBeTruthy())
    unmount()

    getPerfilEmpresa.mockReturnValue(new Promise(() => {}))
    renderizar()

    expect(screen.getByText('moda|true|Departamento')).toBeTruthy()
  })

  it('não busca perfil sem usuário autenticado', () => {
    usuario = null

    renderizar()

    expect(getPerfilEmpresa).not.toHaveBeenCalled()
  })
})
