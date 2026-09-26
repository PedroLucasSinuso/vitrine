import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import BiSubNav from '../bi/BiSubNav'
import RequireModulo from '../RequireModulo'
import { ContextoPerfilEmpresa, PERFIL_PADRAO } from '../../stores/perfilEmpresaContexto'
import type { PerfilEmpresaContexto } from '../../stores/perfilEmpresaContexto'
import type { Modulo, PerfilEmpresa } from '../../types'

vi.mock('../../pages/NotFound', () => ({ default: () => <p>página não encontrada</p> }))

const PERFIL_MODA: PerfilEmpresa = {
  nome: 'Loja',
  segmento: 'moda',
  modo: 'legado',
  modulos: ['dashboard', 'receita', 'ranking', 'curva_abc', 'trocas', 'temporal', 'sku', 'equipe'],
  rotulos: { grupo: 'Departamento', grupos: 'Departamentos', familia: 'Categoria', familias: 'Categorias', documento: 'Atendimento' },
}

function contexto(perfil: PerfilEmpresa, carregado = true): PerfilEmpresaContexto {
  return {
    perfil,
    carregado,
    temModulo: (modulo: Modulo) => perfil.modulos.includes(modulo),
    rotulo: (chave) => perfil.rotulos[chave],
  }
}

function renderizar(ui: React.ReactNode, valor: PerfilEmpresaContexto) {
  return render(
    <MemoryRouter>
      <ContextoPerfilEmpresa.Provider value={valor}>{ui}</ContextoPerfilEmpresa.Provider>
    </MemoryRouter>,
  )
}

describe('navegação do BI por perfil', () => {
  it('supermercado mostra todas as abas de hoje, inclusive Perdas', () => {
    renderizar(<BiSubNav />, contexto(PERFIL_PADRAO))

    expect(screen.getByRole('button', { name: /perdas/i })).toBeTruthy()
    expect(screen.getAllByRole('button')).toHaveLength(8)
  })

  it('moda esconde a aba de Perdas', () => {
    renderizar(<BiSubNav />, contexto(PERFIL_MODA))

    expect(screen.queryByRole('button', { name: /perdas/i })).toBeNull()
    expect(screen.getByRole('button', { name: /receita/i })).toBeTruthy()
  })

  it('sem provider usa o perfil padrão', () => {
    render(<MemoryRouter><BiSubNav /></MemoryRouter>)

    expect(screen.getAllByRole('button')).toHaveLength(8)
  })
})

describe('RequireModulo', () => {
  it('renderiza a página quando a empresa tem o módulo', () => {
    renderizar(<RequireModulo modulo="receita"><p>conteúdo</p></RequireModulo>, contexto(PERFIL_MODA))

    expect(screen.getByText('conteúdo')).toBeTruthy()
  })

  it('mostra não encontrado quando o perfil carregado não tem o módulo', () => {
    renderizar(<RequireModulo modulo="perdas_consumo"><p>conteúdo</p></RequireModulo>, contexto(PERFIL_MODA))

    expect(screen.queryByText('conteúdo')).toBeNull()
    expect(screen.getByText('página não encontrada')).toBeTruthy()
  })

  it('não bloqueia enquanto o perfil ainda não carregou', () => {
    renderizar(
      <RequireModulo modulo="perdas_consumo"><p>conteúdo</p></RequireModulo>,
      contexto(PERFIL_MODA, false),
    )

    expect(screen.getByText('conteúdo')).toBeTruthy()
  })
})
