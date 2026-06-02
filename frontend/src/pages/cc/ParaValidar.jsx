import { useQuery } from '@tanstack/react-query'
import { Loader2, Search, CheckCircle } from 'lucide-react'
import { useState } from 'react'
import Navbar from '../../components/Navbar'
import BottomNav from '../../components/BottomNav'
import VehicleCard from '../../components/VehicleCard'
import { getReprocesos } from '../../api/reprocesos'

export default function ParaValidar() {
  const [searchQuery, setSearchQuery] = useState('')

  const { data: reprocesos, isLoading } = useQuery({
    queryKey: ['reprocesos', 'por_validar'],
    queryFn: () => getReprocesos({ estado: 'por_validar' }),
  })

  const reprocesosFiltrados = (reprocesos || []).filter(rep => {
    if (!searchQuery) return true
    const vinMatch = rep.vin.toLowerCase().includes(searchQuery.toLowerCase())
    const modelMatch = rep.vehiculos?.modelo?.toLowerCase().includes(searchQuery.toLowerCase())
    return vinMatch || modelMatch
  })

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <Navbar />

      <div className="max-w-5xl mx-auto px-4 py-6 animate-fade-in">
        <h1 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <CheckCircle className="w-6 h-6 text-blue-600" />
          Vehículos Para Validar
        </h1>

        <div className="mb-6 relative max-w-md">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por VIN o Modelo..."
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800"
          />
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : (
          <>
            {reprocesosFiltrados.length === 0 ? (
              <div className="text-center py-12 bg-white border border-slate-200 rounded-lg shadow-sm">
                <p className="text-slate-500">No hay vehículos pendientes de validación final.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {reprocesosFiltrados.map((rep) => (
                  <div key={rep.id} onClick={() => window.location.href=`/cc/validar/${rep.id}`} className="cursor-pointer group">
                    <div className="bg-white border border-slate-200 p-4 rounded-xl shadow-sm hover:shadow-md transition-all group-hover:border-blue-300">
                      <p className="font-mono text-blue-600 text-xs font-bold tracking-widest mb-1">{rep.vin}</p>
                      <h3 className="text-slate-900 font-bold mb-1 truncate">{rep.vehiculos?.modelo || 'Desconocido'}</h3>
                      <p className="text-slate-500 text-sm mb-3">Fecha Reproceso: {new Date(rep.creado_en).toLocaleDateString()}</p>
                      <div className="flex items-center justify-between">
                        <span className="bg-amber-100 text-amber-800 px-2 py-0.5 rounded text-xs font-medium border border-amber-200">Por Validar</span>
                        <span className="text-blue-600 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">Validar →</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      <BottomNav />
    </div>
  )
}
