import React, { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
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
import Usuarios from './pages/Usuarios'
import Configuracoes from './pages/Configuracoes'
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

function HomeRouter() {
  const { getRole } = useAuth()
  const role = getRole()
  if (role === 'admin') return <Navigate to="/admin" replace />
  if (role === 'supervisor') return <Navigate to="/home" replace />
  if (role === 'operador') return <Navigate to="/home/operador" replace />
  return <Busca />
}

function App() {
  useEffect(() => {
    const saved = localStorage.getItem('app_darkMode')
    if (saved === 'true') document.documentElement.classList.add('dark')
  }, [])

  return (
    <BrowserRouter>
      <BiCacheProvider>
        <ToastProvider>
          <ErrorBoundary>
            <React.Suspense fallback={<div className="flex items-center justify-center min-h-[60vh] text-gray-400 text-lg">Carregando...</div>}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<ProtectedRoute><HomeRouter /></ProtectedRoute>} />
              <Route path="/busca" element={<ProtectedRoute><Busca /></ProtectedRoute>} />
              <Route path="/home" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><Home /></ProtectedRoute>} />
              <Route path="/home/operador" element={<ProtectedRoute allowedRoles={['operador']}><OperadorHome /></ProtectedRoute>} />
              <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><Admin /></ProtectedRoute>} />
              <Route path="/inventario" element={<ProtectedRoute allowedRoles={['operador', 'supervisor', 'admin']}><Inventario /></ProtectedRoute>} />
              <Route path="/admin/etiquetas" element={<ProtectedRoute allowedRoles={['admin', 'supervisor']}><Etiquetas /></ProtectedRoute>} />
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
              <Route path="*" element={<NotFound />} />
            </Routes>
            </React.Suspense>
          </ErrorBoundary>
          <CmdK />
          <ScrollToTop />
          <ToastContainer />
        </ToastProvider>
      </BiCacheProvider>
    </BrowserRouter>
  )
}

export default App
