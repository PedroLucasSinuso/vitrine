import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
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
  const role = getRole()

  useEffect(() => {
    if (role === 'admin') navigate('/admin', { replace: true })
    else if (role === 'supervisor') navigate('/bi', { replace: true })
    else navigate('/inventario', { replace: true })
  }, [role, navigate])

  return null
}
