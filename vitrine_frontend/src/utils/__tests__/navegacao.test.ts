import { describe, it, expect } from 'vitest'
import { paginaInicial } from '../navegacao'
import { PERFIL_PADRAO } from '../../stores/perfilEmpresaContexto'
import type { PerfilEmpresa } from '../../types'

const perfil = (parcial: Partial<PerfilEmpresa>): PerfilEmpresa => ({ ...PERFIL_PADRAO, ...parcial })

describe('página inicial por perfil', () => {
  it('modo legado segue o papel, como sempre foi', () => {
    expect(paginaInicial('admin', PERFIL_PADRAO)).toBe('/admin')
    expect(paginaInicial('supervisor', PERFIL_PADRAO)).toBe('/bi')
    expect(paginaInicial('operador', PERFIL_PADRAO)).toBe('/inventario')
  })

  it('equipe (upload sem BI de vendas) abre na Equipe para gerente e admin', () => {
    const equipe = perfil({ modo: 'upload', segmento: 'equipe', modulos: ['equipe', 'metas', 'importacao'] })

    expect(paginaInicial('admin', equipe)).toBe('/bi/equipe')
    expect(paginaInicial('supervisor', equipe)).toBe('/bi/equipe')
  })

  it('upload que entregou itens abre no BI', () => {
    const comItens = perfil({ modo: 'upload', segmento: 'moda', modulos: ['dashboard', 'equipe', 'importacao'] })

    expect(paginaInicial('supervisor', comItens)).toBe('/bi')
  })
})
