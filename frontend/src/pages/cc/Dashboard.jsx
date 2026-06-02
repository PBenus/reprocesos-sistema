import { useState, useEffect } from 'react'
import { Search, RefreshCw, Loader2 } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import Navbar from '../../components/Navbar'
import BottomNav from '../../components/BottomNav'
import VehicleCard from '../../components/VehicleCard'
import { getVehiculos } from '../../api/vehiculos'

// 19 zonas ordenadas lógicamente
const PROCESO_ORDER = [
  'ZONA DE INGRESO',
  'ZONA DE ESPERA RECEPCIÓN',
  'PROCESO PDI',
  'ZONA DE ESPERA PROCESO PDI',
  'PINTURA',
  'ZONA DE ESPERA PINTURA',
  'REPUESTO',
  'ZONA DE ESPERA REPUESTOS',
  'BOCAMAZA',
  'ZONA DE ESPERA DE BOCAMAZA',
  'GLP',
  'ZONA DE ESPERA GLP',
  'EQUIPAMIENTO',
  'ZONA DE ESPERA ACONDICIONADO',
  'LAVADO',
  'ZONA DE ESPERA CONTROL DE CALIDAD',
  'LISTOS',
  'LISTOS - REVISADO',
  'DESPACHO',
]

function SkeletonCard() {
  return (
    <div className="card animate-pulse">
      <div className="h-3 bg-slate-200 rounded w-3/4 mb-2" />
      <div className="h-4 bg-slate-200 rounded w-full mb-1" />
      <div className="h-3 bg-slate-200 rounded w-1/2" />
      <div className="flex gap-2 mt-4">
        <div className="h-5 bg-slate-200 rounded-full w-16" />
        <div className="h-5 bg-slate-200 rounded-full w-20" />
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [buscar, setBuscar]   = useState('')
  const [filtrado, setFiltrado] = useState({})

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['vehiculos'],
    queryFn: () => getVehiculos(),
    refetchInterval: 1000 * 60 * 5, // Refresca cada 5 min
  })

  // Filtrar por búsqueda
  useEffect(() => {
    if (!data) return
    const q = buscar.toLowerCase()
    if (!q) { setFiltrado(data); return }
    const result = {}
    for (const [proceso, vins] of Object.entries(data)) {
      const filtered = vins.filter(
        (v) => v.vin?.toLowerCase().includes(q) || v.modelo?.toLowerCase().includes(q)
      )
      if (filtered.length) result[proceso] = filtered
    }
    setFiltrado(result)
  }, [data, buscar])

  const totalVehiculos = Object.values(filtrado).reduce((s, a) => s + a.length, 0)

  // Ordenar procesos según el orden definido
  const procesos = PROCESO_ORDER.filter((p) => filtrado[p]?.length > 0)
  // Agregar procesos desconocidos al final
  const otros = Object.keys(filtrado).filter((p) => !PROCESO_ORDER.includes(p))
  const allProcesos = [...procesos, ...otros]

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <Navbar />

      {/* Header */}
      <div className="max-w-screen-2xl mx-auto px-4 pt-6 pb-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Dashboard de Vehículos</h1>
            <p className="text-slate-500 text-sm mt-0.5">
              {isLoading ? 'Cargando...' : `${totalVehiculos} vehículos en flujo`}
            </p>
          </div>
          <div className="flex items-center gap-3 w-full sm:w-auto">
            {/* Buscador */}
            <div className="relative flex-1 sm:w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Buscar por VIN o modelo..."
                value={buscar}
                onChange={(e) => setBuscar(e.target.value)}
                className="input-field pl-9 text-sm"
              />
            </div>
            {/* Refresh */}
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="btn-secondary px-3 py-2"
              title="Actualizar"
            >
              <RefreshCw className={`w-4 h-4 text-slate-600 ${isFetching ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Kanban scroll horizontal */}
      <div className="max-w-screen-2xl mx-auto px-4 pb-8 overflow-x-auto">
        {isLoading ? (
          <div className="flex gap-4">
            {[1,2,3,4].map((i) => (
              <div key={i} className="min-w-[260px] space-y-3">
                <div className="h-8 bg-slate-200 rounded-lg animate-pulse" />
                {[1,2,3].map((j) => <SkeletonCard key={j} />)}
              </div>
            ))}
          </div>
        ) : allProcesos.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <p className="text-lg font-medium">No se encontraron vehículos</p>
          </div>
        ) : (
          <div className="flex gap-4 pb-2" style={{ minWidth: 'max-content' }}>
            {allProcesos.map((proceso) => {
              const vins = filtrado[proceso] || []
              return (
                <div key={proceso} className="w-[300px] flex-shrink-0">
                  {/* Column header */}
                  <div className="px-1 mb-3 flex items-center gap-2">
                    <span className="text-slate-800 text-base font-medium uppercase tracking-tight">
                      {proceso}
                    </span>
                    <span className="bg-slate-200 text-slate-600 text-xs font-bold px-2 py-0.5 rounded ml-1 flex-shrink-0">
                      {vins.length}
                    </span>
                  </div>
                  {/* Cards */}
                  <div className="space-y-3">
                    {vins.map((v) => <VehicleCard key={v.vin} vehiculo={v} />)}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  )
}
