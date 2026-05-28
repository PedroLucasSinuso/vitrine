import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { tryRefreshOnStartup } from '../api/client'
import { getAccessToken } from '../api/tokenStore'
import type { Role } from '../types'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles: Role[]
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, getRole } = useAuth()
  const [startupDone, setStartupDone] = useState(() => {
    // Se já tem token em memória, startup está completo
    if (getAccessToken()) return true
    // Caso contrário, aguarda o refresh silencioso
    return false
  })

  useEffect(() => {
    if (!startupDone) {
      tryRefreshOnStartup().finally(() => setStartupDone(true))
    }
  }, [startupDone])

  if (!startupDone) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-text-muted">Carregando...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }

  const role = getRole()
  if (!role || !allowedRoles.includes(role)) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}
