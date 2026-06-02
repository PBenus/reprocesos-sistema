import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PaintBucket, Wrench, Clock, Image as ImageIcon, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'
import Navbar from '../../components/Navbar'
import { getMisTrabajosPintura, getMisTrabajosRepuesto } from '../../api/trabajos'

const PAGE_SIZE = 10

export default function Historicos() {
  const { user } = useAuth()
  const tipo     = user?.rol === 'operario_pintura' ? 'pintura' : 'repuesto'
  const [page, setPage]     = useState(1)
  const [filtroVin, setFiltro] = useState('')

  const { data: trabajos = [], isLoading } = useQuery({
    queryKey: ['mis-trabajos', tipo],
    queryFn: tipo === 'pintura' ? getMisTrabajosPintura : getMisTrabajosRepuesto,
  })

  const filtrados = filtroVin
    ? trabajos.filter((t) => t.vin?.toLowerCase().includes(filtroVin.toLowerCase()))
    : trabajos

  const totalPages = Math.ceil(filtrados.length / PAGE_SIZE)
  const paginados  = filtrados.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const Icon  = tipo === 'pintura' ? PaintBucket : Wrench
  const color = tipo === 'pintura' ? 'text-amber-500' : 'text-blue-600'
  const titulo = tipo === 'pintura' ? 'PINTURA' : 'REPUESTO'

  function duracion(abierto, cerrado) {
    if (!abierto || !cerrado) return '—'
    try {
      const mins = Math.round((new Date(cerrado) - new Date(abierto)) / 60000)
      return mins < 60 ? `${mins} min` : `${Math.floor(mins/60)}h ${mins%60}min`
    } catch { return '—' }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white shadow-sm rounded-xl flex items-center justify-center border border-slate-200">
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Historial — {titulo}</h1>
              <p className="text-slate-500 text-sm font-medium">{filtrados.length} trabajos completados</p>
            </div>
          </div>
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar por VIN..."
              value={filtroVin}
              onChange={(e) => { setFiltro(e.target.value); setPage(1) }}
              className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 text-slate-800"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[1,2,3].map((i) => <div key={i} className="bg-slate-200 animate-pulse h-28 rounded-2xl" />)}
          </div>
        ) : !paginados.length ? (
          <div className="bg-white border border-slate-200 rounded-2xl text-center py-12 shadow-sm">
            <p className="text-slate-500">No hay trabajos históricos aún.</p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {paginados.map((t) => (
                <div key={t.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="font-mono text-blue-600 text-xs font-bold tracking-widest mb-1">{t.vin}</p>
                      <p className="text-slate-900 font-bold">{t.modelo || 'Vehículo'}</p>
                      {t.seccion && <p className="text-slate-500 text-xs mt-0.5 font-medium">{t.seccion}</p>}
                      <p className="text-slate-500 text-sm mt-1">{t.observacion_item || '—'}</p>
                      {t.nombre_creador && (
                        <p className="text-slate-400 text-xs mt-2 font-medium">Reportado por CC: {t.nombre_creador}</p>
                      )}
                      {t.nombre_operario && (
                        <p className="text-slate-400 text-xs font-medium">Operario: {t.nombre_operario}</p>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-2 flex-shrink-0">
                      <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded text-xs font-bold border border-green-200">
                        Subsanado
                      </span>
                      <span className="flex items-center gap-1 text-slate-400 text-xs font-medium">
                        <Clock className="w-3.5 h-3.5" /> {duracion(t.abierto_en, t.cerrado_en)}
                      </span>
                    </div>
                  </div>
                  {t.notas && <p className="text-slate-500 text-xs mt-3 bg-slate-50 p-2 rounded border border-slate-100">"{t.notas}"</p>}
                  {t.foto_url && (
                    <a href={t.foto_url} target="_blank" rel="noreferrer"
                       className="mt-4 inline-flex items-center gap-1.5 text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors">
                      <ImageIcon className="w-4 h-4" /> Ver foto del resultado
                    </a>
                  )}
                  <div className="flex gap-4 mt-4 pt-4 border-t border-slate-100">
                    <span className="text-slate-400 text-xs">
                      <strong className="text-slate-600">Iniciado:</strong> {t.abierto_en ? new Date(t.abierto_en).toLocaleString('es-PE') : '—'}
                    </span>
                    <span className="text-slate-400 text-xs">
                      <strong className="text-slate-600">Cerrado:</strong> {t.cerrado_en ? new Date(t.cerrado_en).toLocaleString('es-PE') : '—'}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-3 mt-8">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-5 h-5" />
                </button>
                <span className="text-slate-500 text-sm font-medium">
                  Página {page} de {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
