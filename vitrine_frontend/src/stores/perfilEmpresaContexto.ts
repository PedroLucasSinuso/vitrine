import { createContext, useContext } from 'react'
import type { ChaveRotulo, Modulo, PerfilEmpresa } from '../types'

export const PERFIL_PADRAO: PerfilEmpresa = {
  nome: '',
  segmento: 'supermercado',
  modo: 'legado',
  modulos: [
    'dashboard', 'receita', 'ranking', 'curva_abc', 'trocas', 'perdas_consumo',
    'temporal', 'sku', 'busca', 'produtos', 'inventario', 'etiquetas',
  ],
  rotulos: { grupo: 'Grupo', grupos: 'Grupos', familia: 'Família', familias: 'Famílias', documento: 'Cupom' },
}

export interface PerfilEmpresaContexto {
  perfil: PerfilEmpresa
  carregado: boolean
  pronto?: boolean
  temModulo: (modulo: Modulo) => boolean
  rotulo: (chave: ChaveRotulo) => string
}

export const ContextoPerfilEmpresa = createContext<PerfilEmpresaContexto | null>(null)

export function usePerfilEmpresa(): PerfilEmpresaContexto {
  const contexto = useContext(ContextoPerfilEmpresa)
  if (contexto) return contexto
  return {
    perfil: PERFIL_PADRAO,
    carregado: false,
    temModulo: (modulo) => PERFIL_PADRAO.modulos.includes(modulo),
    rotulo: (chave) => PERFIL_PADRAO.rotulos[chave],
  }
}
