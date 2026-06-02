import { useQuery } from '@tanstack/react-query'
import { Loader2, Search, Car } from 'lucide-react'
import { useState } from 'react'
import Navbar from '../../components/Navbar'
import BottomNav from '../../components/BottomNav'
import VehicleCard from '../../components/VehicleCard'
import { getReprocesos } from '../../api/reprocesos'

export default function HistoricoCC() {
  const [searchQuery, setSearchQuery] = useState('')

  const { data: reprocesos, isLoading } = useQuery({
    queryKey: ['reprocesos', 'historico_cc'],
    queryFn: () => getReprocesos({ estado: 'cerrado' }),
  })

  // Extract unique vehicles that have reprocesos
  // Note: the backend now returns reprocesos with nested 'vehiculos' object
  let vehiculosUnicos = []
  if (reprocesos) {
    const mapaVehiculos = new Map()
    for (const rep of reprocesos) {
      if (rep.vehiculos && !mapaVehiculos.has(rep.vin)) {
        mapaVehiculos.set(rep.vin, rep.vehiculos)
      }
    }
    vehiculosUnicos = Array.from(mapaVehiculos.values())
  }

  const vehiculosFiltrados = vehiculosUnicos.filter(v =>
    searchQuery === '' ||
    v.vin.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (v.modelo || '').toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <Navbar />

      <div className="max-w-5xl mx-auto px-4 py-6 animate-fade-in">
        <h1 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <Car className="w-6 h-6 text-blue-600" />
          Historial de Vehículos con Reprocesos
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
            {vehiculosFiltrados.length === 0 ? (
              <div className="text-center py-12 bg-white border border-slate-200 rounded-lg shadow-sm">
                <p className="text-slate-500">No hay vehículos con reprocesos para mostrar.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {vehiculosFiltrados.map((vehiculo) => (
                  <VehicleCard key={vehiculo.vin} vehiculo={vehiculo} />
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
