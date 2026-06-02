import { useNavigate } from 'react-router-dom'
import { Heart, Share2 } from 'lucide-react'

export default function VehicleCard({ vehiculo }) {
  const navigate = useNavigate()

  // Ejemplo de mensaje superior basado en estado o campos vacíos
  const mensajeSuperior = vehiculo.observaciones || "Nadie ha iniciado el control de calidad todavía."

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-col gap-5">
      
      {/* Top section: Mensaje y Concesionario */}
      <div>
        <p className="text-slate-900 font-bold text-[13px] leading-tight mb-1">
          {mensajeSuperior}
        </p>
        <p className="text-slate-400 text-[11px] uppercase tracking-wide">
          {vehiculo.concesionario || 'CONCESIONARIO NO REGISTRADO'}
        </p>
      </div>

      {/* Middle section: VIN, Marca, Modelo, Color */}
      <div>
        <p className="font-mono text-slate-800 text-xl font-normal tracking-wide mb-1">
          {vehiculo.vin}
        </p>
        <p className="text-slate-500 text-xs uppercase tracking-wide mb-3">
          {vehiculo.marca}
        </p>
        <p className="text-slate-700 text-sm font-medium uppercase leading-snug">
          {vehiculo.modelo} {vehiculo.color ? `- ${vehiculo.color}` : ''}
        </p>
      </div>

      {/* Bottom section: Acciones */}
      <div className="flex items-center justify-between mt-1">
        <button 
          onClick={() => navigate(`/cc/vehiculo/${vehiculo.vin}`)}
          className="text-blue-600 font-medium text-[13px] hover:text-blue-700 transition-colors"
        >
          VER DETALLES
        </button>
        <div className="flex items-center gap-4 text-slate-600">
          <button className="hover:text-red-500 transition-colors">
            <Heart className="w-5 h-5" />
          </button>
          <button className="hover:text-blue-500 transition-colors">
            <Share2 className="w-5 h-5" />
          </button>
        </div>
      </div>

    </div>
  )
}
