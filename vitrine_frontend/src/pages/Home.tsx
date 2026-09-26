import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePerfilEmpresa } from '../stores/perfilEmpresaContexto'
import { paginaInicial } from '../utils/navegacao'
import { useAuth } from '../hooks/useAuth'

/**
 * Home — redireciona para a página mais relevante baseada no perfil.
 *
 * admin      → /admin (Sync ETL)
 * supervisor → /bi (Dashboard Consolidado)
 * operador   → /inventario (Inventário)
 *
 * Se não houver role (não autenticado), o AppLayout já cuida do redirect
 * para /login via ProtectedRoute.
 */
export default function Home() {
  const navigate = useNavigate()
  const { getRole } = useAuth()
  const { perfil, pronto } = usePerfilEmpresa()
  const role = getRole()

  useEffect(() => {
    if (pronto === false) return
    navigate(paginaInicial(role, perfil), { replace: true })
  }, [role, perfil, pronto, navigate])

  return null
}
