import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Car, LogOut, History, ClipboardList, LayoutDashboard, ChevronRight, Loader2, RefreshCw } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useMutation } from '@tanstack/react-query'
import client from '../api/client'

const ROL_LABEL = {
  control_calidad:   { text: 'Control de Calidad', color: 'badge-blue' },
  operario_pintura:  { text: 'Operario Pintura',   color: 'badge-yellow' },
  operario_repuesto: { text: 'Operario Repuesto',  color: 'badge-green' },
}

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const rolInfo  = ROL_LABEL[user?.rol] || { text: user?.rol, color: 'badge-gray' }

  const syncMutation = useMutation({
    mutationFn: async () => {
      const res = await client.post('/sync/force')
      return res.data
    },
    onSuccess: () => {
      alert('Sincronización iniciada en segundo plano.')
    },
    onError: (err) => {
      alert('Error: ' + (err.response?.data?.detail || err.message))
    }
  })

  const isCC       = user?.rol === 'control_calidad'
  const isOperario = user?.rol === 'operario_pintura' || user?.rol === 'operario_repuesto'

  const navLinks = isCC
    ? [{ to: '/cc/dashboard', label: 'Dashboard', icon: LayoutDashboard }]
    : [
        { to: '/operario/pendientes', label: 'Pendientes',  icon: ClipboardList },
        { to: '/operario/historicos', label: 'Históricos',  icon: History },
      ]

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-screen-2xl mx-auto px-4 h-14 flex items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center shadow">
            <Car className="w-4 h-4 text-white" />
          </div>
          <div className="hidden sm:block">
            <span className="font-bold text-slate-800 text-sm">Reprocesos</span>
            <span className="text-slate-500 text-xs block leading-none">VARI OVALO</span>
          </div>
        </div>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {navLinks.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                ${location.pathname.startsWith(to)
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'}`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{label}</span>
            </Link>
          ))}
        </div>

        {/* User info + logout */}
        <div className="flex items-center gap-3">
          {isCC && (
            <button
              onClick={() => syncMutation.mutate()}
              disabled={syncMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-500 hover:text-blue-700 hover:bg-blue-50 transition-all"
              title="Sincronizar eSUM"
            >
              {syncMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            </button>
          )}
          <div className="hidden md:flex flex-col items-end">
            <span className="text-slate-800 text-sm font-medium leading-none">{user?.nombre}</span>
            <span className={`${rolInfo.color} mt-1 text-[10px]`}>{rolInfo.text}</span>
          </div>
          <button
            onClick={logout}
            title="Cerrar sesión"
            className="flex items-center gap-1.5 text-slate-500 hover:text-red-600 hover:bg-red-50
                       px-3 py-1.5 rounded-lg transition-all text-sm font-medium"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline">Salir</span>
          </button>
        </div>
      </div>
    </nav>
  )
}
