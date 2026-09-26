import type { PerfilEmpresa } from '../types'

const PREFIXO_CACHE = 'vitrine_perfil:'

export function lerCache(username: string): PerfilEmpresa | null {
  try {
    const bruto = localStorage.getItem(PREFIXO_CACHE + username)
    return bruto ? (JSON.parse(bruto) as PerfilEmpresa) : null
  } catch {
    return null
  }
}

export function gravarCache(username: string, perfil: PerfilEmpresa) {
  try {
    localStorage.setItem(PREFIXO_CACHE + username, JSON.stringify(perfil))
  } catch {
    return
  }
}

export function limparCachePerfil() {
  try {
    Object.keys(localStorage)
      .filter((chave) => chave.startsWith(PREFIXO_CACHE))
      .forEach((chave) => localStorage.removeItem(chave))
  } catch {
    return
  }
}
