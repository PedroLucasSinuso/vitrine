import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import { getPerfilEmpresa } from '../api/empresa'
import { useAuth } from '../hooks/useAuth'
import type { ChaveRotulo, Modulo, PerfilEmpresa } from '../types'
import { gravarCache, lerCache } from '../utils/perfilCache'
import { NOME_DO_EVENTO_PERFIL } from '../utils/navegacao'
import { ContextoPerfilEmpresa, PERFIL_PADRAO } from './perfilEmpresaContexto'

export function PerfilEmpresaProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, getUsername } = useAuth()
  useLocation()
  const username = isAuthenticated() ? getUsername() : null
  const [estado, setEstado] = useState<{ username: string | null; perfil: PerfilEmpresa | null; falhou: boolean }>({
    username: null,
    perfil: null,
    falhou: false,
  })
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    const atualizar = () => setVersao((v) => v + 1)
    window.addEventListener(NOME_DO_EVENTO_PERFIL, atualizar)
    return () => window.removeEventListener(NOME_DO_EVENTO_PERFIL, atualizar)
  }, [])

  useEffect(() => {
    if (!username) return
    let cancelado = false
    getPerfilEmpresa()
      .then((perfil) => {
        if (cancelado) return
        gravarCache(username, perfil)
        setEstado({ username, perfil, falhou: false })
      })
      .catch(() => {
        if (!cancelado) setEstado((atual) => ({ ...atual, username, falhou: true }))
      })
    return () => {
      cancelado = true
    }
  }, [username, versao])

  const perfilAtual = useMemo(() => {
    if (!username) return null
    if (estado.username === username && estado.perfil) return estado.perfil
    return lerCache(username)
  }, [username, estado])
  const perfil = perfilAtual ?? PERFIL_PADRAO

  const temModulo = useCallback((modulo: Modulo) => perfil.modulos.includes(modulo), [perfil])
  const rotulo = useCallback((chave: ChaveRotulo) => perfil.rotulos[chave] ?? PERFIL_PADRAO.rotulos[chave], [perfil])

  const valor = useMemo(
    () => ({
      perfil,
      carregado: perfilAtual !== null,
      pronto: perfilAtual !== null || estado.falhou || username === null,
      temModulo,
      rotulo,
    }),
    [perfil, perfilAtual, estado.falhou, username, temModulo, rotulo],
  )

  return <ContextoPerfilEmpresa.Provider value={valor}>{children}</ContextoPerfilEmpresa.Provider>
}
