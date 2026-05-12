import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import type { Role } from '../types'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: Role[]
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, getRole } = useAuth()

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles) {
    const role = getRole()
    if (!role || !allowedRoles.includes(role)) {
      return <Navigate to="/" replace />
    }
  }

  return <>{children}</>
}
