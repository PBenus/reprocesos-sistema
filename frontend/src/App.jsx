import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'

import Login              from './pages/Login'
import Dashboard          from './pages/cc/Dashboard'
import HistoricoCC        from './pages/cc/HistoricoCC'
import ParaValidar        from './pages/cc/ParaValidar'
import ValidarReproceso   from './pages/cc/ValidarReproceso'
import VehicleDetail      from './pages/cc/VehicleDetail'
import IniciarReproceso   from './pages/cc/IniciarReproceso'
import Pendientes         from './pages/operario/Pendientes'
import Historicos         from './pages/operario/Historicos'

// ── Protected Route ────────────────────────────────────────────
function ProtectedRoute({ children, allowedRoles }) {
  const { user, isLoading } = useAuth()
  if (isLoading) return <LoadingScreen />
  if (!user) return <Navigate to="/login" replace />
  if (allowedRoles && !allowedRoles.includes(user.rol))
    return <Navigate to="/unauthorized" replace />
  return children
}

function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-slate-400 text-sm">Cargando...</p>
      </div>
    </div>
  )
}

function RoleRedirect() {
  const { user, isLoading } = useAuth()
  if (isLoading) return <LoadingScreen />
  if (!user) return <Navigate to="/login" replace />
  if (user.rol === 'control_calidad') return <Navigate to="/cc/dashboard" replace />
  return <Navigate to="/operario/pendientes" replace />
}

// ── App ────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<RoleRedirect />} />

        {/* Control de Calidad */}
        <Route path="/cc/dashboard" element={
          <ProtectedRoute allowedRoles={['control_calidad']}>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/cc/validar" element={
          <ProtectedRoute allowedRoles={['control_calidad']}>
            <ParaValidar />
          </ProtectedRoute>
        } />
        <Route path="/cc/validar/:id" element={
          <ProtectedRoute allowedRoles={['control_calidad']}>
            <ValidarReproceso />
          </ProtectedRoute>
        } />
        <Route path="/cc/historico" element={
          <ProtectedRoute allowedRoles={['control_calidad']}>
            <HistoricoCC />
          </ProtectedRoute>
        } />
        <Route path="/cc/vehiculo/:vin" element={
          <ProtectedRoute allowedRoles={['control_calidad']}>
            <VehicleDetail />
          </ProtectedRoute>
        } />
        <Route path="/cc/reproceso/nuevo/:vin" element={
          <ProtectedRoute allowedRoles={['control_calidad']}>
            <IniciarReproceso />
          </ProtectedRoute>
        } />

        {/* Operarios */}
        <Route path="/operario/pendientes" element={
          <ProtectedRoute allowedRoles={['operario_pintura', 'operario_repuesto']}>
            <Pendientes />
          </ProtectedRoute>
        } />
        <Route path="/operario/historicos" element={
          <ProtectedRoute allowedRoles={['operario_pintura', 'operario_repuesto']}>
            <Historicos />
          </ProtectedRoute>
        } />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
