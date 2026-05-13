import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Busca from './pages/Busca'
import Admin from './pages/Admin'
import Etiquetas from './pages/Etiquetas'
import Inventario from './pages/Inventario'
import Home from './pages/Home'
import NotFound from './pages/NotFound'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './hooks/useAuth'
import Usuarios from './pages/Usuarios'
import Configuracoes from './pages/Configuracoes'
import BiDashboard from './pages/bi/Dashboard'
import BiReceita from './pages/bi/Receita'
import BiCurvaAbc from './pages/bi/CurvaAbc'
import BiRanking from './pages/bi/Ranking'
import BiTrocas from './pages/bi/Trocas'
import BiPerdasConsumo from './pages/bi/PerdasConsumo'
import BiTemporal from './pages/bi/Temporal'
import BiSku from './pages/bi/Sku'
import { BiCacheProvider } from './stores/biCache'
import { ToastProvider } from './hooks/useToast'
import ToastContainer from './components/ToastContainer'
import ScrollToTop from './components/ui/ScrollToTop'

function HomeRouter() {
  const { getRole } = useAuth()
  const role = getRole()
  if (role === 'admin') return <Navigate to="/admin" replace />
  if (role === 'supervisor') return <Navigate to="/home" replace />
  return <Busca />
}

function App() {
  useEffect(() => {
    const saved = localStorage.getItem('darkMode')
    if (saved === 'true') document.documentElement.classList.add('dark')
  }, [])

  return (
    <BrowserRouter>
      <BiCacheProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<ProtectedRoute><HomeRouter /></ProtectedRoute>} />
            <Route path="/busca" element={<ProtectedRoute><Busca /></ProtectedRoute>} />
            <Route path="/home" element={<ProtectedRoute allowedRoles={['supervisor', 'admin']}><Home /></ProtectedRoute>} />
            <Route path="/admin" element={<ProtectedRoute allowedRoles={['admin']}><Admin /></ProtectedRoute>} />
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
          <ScrollToTop />
          <ToastContainer />
        </ToastProvider>
      </BiCacheProvider>
    </BrowserRouter>
  )
}

export default App
