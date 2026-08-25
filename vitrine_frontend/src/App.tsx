import React from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import Login from './pages/Login'
import Busca from './pages/Busca'
import Admin from './pages/Admin'
import Etiquetas from './pages/Etiquetas'
import Inventario from './pages/Inventario'
import OperadorHome from './pages/OperadorHome'
import Home from './pages/Home'
import NotFound from './pages/NotFound'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './hooks/useAuth'
import { hasRole } from './utils/auth'
import Usuarios from './pages/Usuarios'
import Configuracoes from './pages/Configuracoes'
import Produtos from './pages/Produtos'
const BiDashboard = React.lazy(() => import('./pages/bi/Dashboard'))
const BiReceita = React.lazy(() => import('./pages/bi/Receita'))
const BiCurvaAbc = React.lazy(() => import('./pages/bi/CurvaAbc'))
const BiRanking = React.lazy(() => import('./pages/bi/Ranking'))
const BiTrocas = React.lazy(() => import('./pages/bi/Trocas'))
const BiPerdasConsumo = React.lazy(() => import('./pages/bi/PerdasConsumo'))
const BiTemporal = React.lazy(() => import('./pages/bi/Temporal'))
const BiSku = React.lazy(() => import('./pages/bi/Sku'))
import { BiCacheProvider } from './stores/biCache'
import { ToastProvider } from './hooks/useToast'
import ToastContainer from './components/ToastContainer'
import ScrollToTop from './components/ui/ScrollToTop'
import CmdK from './components/ui/CmdK'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ThemeProvider } from './themes/ThemeProvider'
import AppLayout from './components/layout/AppLayout'
import Landing from './pages/Landing'

/** A raiz é pública: visitante anônimo vê a landing, usuário logado cai
 *  direto na tela inicial do papel dele. */
function Raiz() {
  const { isAuthenticated, getRole } = useAuth()
  if (!isAuthenticated()) return <Landing />

  const role = getRole()
  if (hasRole(role, ['admin'])) return <Navigate to="/admin" replace />
  if (hasRole(role, ['supervisor'])) return <Navigate to="/home" replace />
  if (hasRole(role, ['operador'])) return <Navigate to="/home/operador" replace />
  return <Navigate to="/busca" replace />
}

/** Escuta o evento auth:unauthorized disparado pelo interceptor 401
 *  e redireciona via React Router (sem full page reload). */
function AuthListener() {
  const navigate = useNavigate()
  React.useEffect(() => {
    const handler = () => navigate('/login', { replace: true })
    window.addEventListener('auth:unauthorized', handler)
    return () => window.removeEventListener('auth:unauthorized', handler)
  }, [navigate])
  return null
}

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
      <BiCacheProvider>
        <ToastProvider>
          <ErrorBoundary>
            <AuthListener />
            <React.Suspense fallback={<div className="flex items-center justify-center min-h-[60vh] text-gray-400 text-lg">Carregando...</div>}>
            <Routes>
              <Route path="/" element={<Raiz />} />
              <Route path="/login" element={<Login />} />
              <Route element={<AppLayout />}>
                <Route path="/busca" element={<ProtectedRoute allowedRoles={['admin', 'supervisor', 'operador']}><Busca /></ProtectedRoute>} />
                <Route path="/home" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><Home /></ProtectedRoute>} />
                <Route path="/home/operador" element={<ProtectedRoute allowedRoles={['operador']}><OperadorHome /></ProtectedRoute>} />
                <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><Admin /></ProtectedRoute>} />
                <Route path="/inventario" element={<ProtectedRoute allowedRoles={['operador', 'supervisor', 'admin']}><Inventario /></ProtectedRoute>} />
                <Route path="/produtos" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><Produtos /></ProtectedRoute>} />
                <Route path="/etiquetas" element={<ProtectedRoute allowedRoles={['operador', 'supervisor', 'admin']}><Etiquetas /></ProtectedRoute>} />
                <Route path="/admin/etiquetas" element={<Navigate to="/etiquetas" replace />} />
                <Route path="/admin/inventario" element={<ProtectedRoute allowedRoles={['admin', 'supervisor', 'operador']}><Inventario /></ProtectedRoute>} />
                <Route path="/admin/usuarios" element={<ProtectedRoute allowedRoles={['admin']}><Usuarios /></ProtectedRoute>} />
                <Route path="/admin/configuracoes" element={<ProtectedRoute allowedRoles={['admin']}><Configuracoes /></ProtectedRoute>} />
                <Route path="/bi" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><BiDashboard /></ProtectedRoute>} />
                <Route path="/bi/receita" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><BiReceita /></ProtectedRoute>} />
                <Route path="/bi/curva-abc" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><BiCurvaAbc /></ProtectedRoute>} />
                <Route path="/bi/ranking" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><BiRanking /></ProtectedRoute>} />
                <Route path="/bi/trocas" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><BiTrocas /></ProtectedRoute>} />
                <Route path="/bi/perdas-consumo" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><BiPerdasConsumo /></ProtectedRoute>} />
                <Route path="/bi/temporal" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><BiTemporal /></ProtectedRoute>} />
                <Route path="/bi/sku" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><BiSku /></ProtectedRoute>} />
                <Route path="/bi/dashboard-consolidado" element={<Navigate to="/bi" replace />} />
              </Route>
              <Route path="*" element={<NotFound />} />
            </Routes>
            </React.Suspense>
          </ErrorBoundary>
          <CmdK />
          <ScrollToTop />
          <ToastContainer />
        </ToastProvider>
      </BiCacheProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App
