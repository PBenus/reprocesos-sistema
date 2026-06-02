import { useNavigate, useLocation } from 'react-router-dom'
import { Car, History, CheckCircle } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

export default function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()
  
  const isVehiculos = location.pathname.includes('/cc/dashboard')
  const isValidar = location.pathname.includes('/cc/validar')
  const isHistorico = location.pathname.includes('/cc/historico')

  if (user?.rol !== 'control_calidad') return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-2 py-2 flex justify-around shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-50">
      <button
        onClick={() => navigate('/cc/dashboard')}
        className={`flex flex-col items-center gap-1 px-4 py-1 transition-colors ${
          isVehiculos ? 'text-blue-600' : 'text-slate-500 hover:text-slate-800'
        }`}
      >
        <Car className="w-6 h-6" />
        <span className="text-[10px] font-semibold">Vehículos</span>
      </button>

      <button
        onClick={() => navigate('/cc/validar')}
        className={`flex flex-col items-center gap-1 px-4 py-1 transition-colors ${
          isValidar ? 'text-blue-600' : 'text-slate-500 hover:text-slate-800'
        }`}
      >
        <CheckCircle className="w-6 h-6" />
        <span className="text-[10px] font-semibold">Para Validar</span>
      </button>

      <button
        onClick={() => navigate('/cc/historico')}
        className={`flex flex-col items-center gap-1 px-4 py-1 transition-colors ${
          isHistorico ? 'text-blue-600' : 'text-slate-500 hover:text-slate-800'
        }`}
      >
        <History className="w-6 h-6" />
        <span className="text-[10px] font-semibold">Historial</span>
      </button>
    </div>
  )
}
