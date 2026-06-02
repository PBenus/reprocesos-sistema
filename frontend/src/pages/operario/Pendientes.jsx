import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  PaintBucket, Wrench, Play, X, CheckCircle2, Loader2,
  Car, MapPin, Palette, Building2, ChevronRight, Camera, FileText, ArrowLeft
} from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'
import Navbar from '../../components/Navbar'
import FotoUploader from '../../components/FotoUploader'
import { getReprocesos, getReproceso } from '../../api/reprocesos'
import {
  iniciarTrabajoPintura, cerrarTrabajoPintura,
  iniciarTrabajoRepuesto, cerrarTrabajoRepuesto,
} from '../../api/trabajos'

// ─── Ficha del vehículo ────────────────────────────────────────────────────
function VehicleInfo({ vehiculo }) {
  if (!vehiculo) return null
  const fields = [
    { icon: Car,       label: 'Modelo',        value: vehiculo.modelo },
    { icon: Palette,   label: 'Color',         value: vehiculo.color },
    { icon: Building2, label: 'Concesionario', value: vehiculo.concesionario },
    { icon: MapPin,    label: 'Taller',        value: vehiculo.taller },
    { icon: Car,       label: 'Marca',         value: vehiculo.marca },
    { icon: FileText,  label: 'Proceso',       value: vehiculo.proceso },
  ]
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 grid grid-cols-2 gap-x-6 gap-y-2">
      {fields.map(({ icon: Icon, label, value }) => value ? (
        <div key={label} className="flex items-center gap-2 min-w-0">
          <Icon className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
          <div className="min-w-0">
            <p className="text-[10px] text-slate-400 uppercase font-bold tracking-wider leading-none">{label}</p>
            <p className="text-slate-800 text-xs font-semibold truncate mt-0.5">{value}</p>
          </div>
        </div>
      ) : null)}
    </div>
  )
}

// ─── Modal de trabajo ítem por ítem ────────────────────────────────────────
function TrabajoModal({ reprocesoId, tipo, onClose, onDone }) {
  const [activeItemId, setActiveItemId] = useState(null)
  const [trabajoActivo, setTrabajoActivo] = useState(null) // { id, item_id }
  const [fotoUrl, setFotoUrl]   = useState(null)
  const [notas, setNotas]       = useState('')
  const [elapsed, setElapsed]   = useState(0)
  const [timerRef, setTimerRef] = useState(null)
  const [doneItems, setDoneItems] = useState([]) // ids de ítems ya subsanados en esta sesión
  const qc = useQueryClient()

  const { data: reproceso, isLoading } = useQuery({
    queryKey: ['reproceso', reprocesoId],
    queryFn: () => getReproceso(reprocesoId),
    enabled: !!reprocesoId,
  })

  const allItems = tipo === 'pintura'
    ? (reproceso?.items_pintura || [])
    : (reproceso?.items_repuesto || [])

  const pendientes = allItems.filter(i => i.estado === 'pendiente' && !doneItems.includes(i.id))
  const todoListo  = pendientes.length === 0 && allItems.length > 0

  const iniciar = tipo === 'pintura' ? iniciarTrabajoPintura : iniciarTrabajoRepuesto
  const cerrar  = tipo === 'pintura' ? cerrarTrabajoPintura  : cerrarTrabajoRepuesto

  const startMut = useMutation({
    mutationFn: (item_id) => iniciar(item_id),
    retry: false, // No reintentar — evita doble apertura
    onSuccess: (data) => {
      setTrabajoActivo(data)
      const start = Date.now()
      const t = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000)
      setTimerRef(t)
    },
    onError: (err) => {
      const detail = err.response?.data?.detail || err.message || ''
      // Si ya existe un trabajo abierto, recuperarlo
      if (detail.includes('ya está en estado') || detail.includes('ya existe un trabajo')) {
        alert('Este ítem ya fue iniciado. Recarga la página si no ves el trabajo activo.')
      } else {
        alert('Error al iniciar: ' + detail)
      }
    }
  })

  const _handleCerrado = () => {
    clearInterval(timerRef)
    setDoneItems(prev => [...prev, activeItemId])
    setTrabajoActivo(null)
    setActiveItemId(null)
    setFotoUrl(null)
    setNotas('')
    setElapsed(0)
    qc.invalidateQueries({ queryKey: ['reprocesos'] })
    qc.invalidateQueries({ queryKey: ['reproceso', reprocesoId] })
  }

  const closeMut = useMutation({
    mutationFn: () => cerrar(trabajoActivo.id, { foto_url: fotoUrl, notas }),
    retry: false, // No reintentar — evita el doble cierre
    onSuccess: _handleCerrado,
    onError: (err) => {
      const detail = err.response?.data?.detail || err.message || ''
      // Si el trabajo ya fue cerrado en el backend (reintento de red), tratar como éxito
      if (detail.includes('ya fue cerrado') || detail.includes('ya fue cerrado')) {
        _handleCerrado()
      } else {
        alert('Error al cerrar: ' + detail)
      }
    }
  })

  const handleEmpezarItem = (item) => {
    setActiveItemId(item.id)
    startMut.mutate(item.id)
  }

  const fmt = (s) => `${Math.floor(s/60).toString().padStart(2,'0')}:${(s%60).toString().padStart(2,'0')}`

  if (isLoading || !reproceso) return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-8 flex flex-col items-center shadow-2xl border border-slate-200">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-3" />
        <p className="text-slate-500 text-sm font-medium">Cargando detalles del reproceso...</p>
      </div>
    </div>
  )

  const vehiculo = reproceso.vehiculos

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-3 sm:p-4">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-lg shadow-2xl animate-slide-up flex flex-col max-h-[95vh]">

        {/* Header fijo */}
        <div className="flex items-start justify-between p-5 border-b border-slate-100 flex-shrink-0">
          <div className="flex-1 min-w-0">
            <p className="font-mono text-blue-600 text-xs font-bold tracking-widest">{reproceso.vin}</p>
            <h3 className="text-slate-900 font-bold text-base mt-0.5 truncate">
              {vehiculo?.modelo || 'Vehículo sin modelo'}
            </h3>
            {reproceso.notas_cc && (
              <p className="text-slate-500 text-xs italic mt-1 bg-amber-50 border border-amber-100 rounded px-2 py-1">
                📋 CC: "{reproceso.notas_cc}"
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 ml-3">
            {trabajoActivo && (
              <div className="flex items-center gap-1.5 bg-green-50 text-green-700 border border-green-200 rounded-full px-2.5 py-1 text-xs font-mono font-bold">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                {fmt(elapsed)}
              </div>
            )}
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors p-1">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body con scroll */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">

          {/* Ficha del vehículo */}
          <VehicleInfo vehiculo={vehiculo} />

          {/* ── Vista de lista de ítems (sin ítem activo) ── */}
          {!activeItemId && (
            <>
              {todoListo ? (
                <div className="text-center py-8 animate-fade-in">
                  <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <CheckCircle2 className="w-7 h-7 text-green-600" />
                  </div>
                  <p className="text-slate-900 font-bold text-base">¡Todos los daños subsanados!</p>
                  <p className="text-slate-500 text-sm mt-1">Este reproceso ha quedado completado.</p>
                  <button onClick={onDone} className="mt-4 btn-primary justify-center px-6">
                    Cerrar
                  </button>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between">
                    <h4 className="text-slate-700 text-sm font-bold">
                      Daños a subsanar
                    </h4>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      tipo === 'pintura'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {pendientes.length} pendiente(s)
                    </span>
                  </div>
                  <div className="space-y-2">
                    {allItems.map((item) => {
                      const isDone = doneItems.includes(item.id) || item.estado === 'subsanado'
                      const isEnProceso = item.estado === 'en_proceso'
                      return (
                        <div key={item.id}
                          className={`rounded-xl border p-3.5 transition-all ${
                            isDone
                              ? 'bg-green-50 border-green-200 opacity-70'
                              : isEnProceso
                              ? 'bg-blue-50 border-blue-200'
                              : 'bg-white border-slate-200 hover:border-blue-300 hover:shadow-sm cursor-pointer'
                          }`}
                          onClick={() => !isDone && !isEnProceso && handleEmpezarItem(item)}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                              {item.seccion && (
                                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-0.5">{item.seccion}</p>
                              )}
                              <p className="text-slate-900 text-sm font-semibold leading-snug">{item.observacion || 'Sin observación'}</p>
                            </div>
                            <div className="flex-shrink-0 flex items-center">
                              {isDone ? (
                                <span className="flex items-center gap-1 text-green-600 text-xs font-bold">
                                  <CheckCircle2 className="w-4 h-4" /> Hecho
                                </span>
                              ) : isEnProceso ? (
                                <span className="text-blue-600 text-xs font-bold">En proceso</span>
                              ) : startMut.isPending && activeItemId === item.id ? (
                                <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                              ) : (
                                <span className="flex items-center gap-1 text-blue-600 text-xs font-semibold group-hover:underline">
                                  <Play className="w-3.5 h-3.5" /> Empezar
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </>
              )}
            </>
          )}

          {/* ── Vista activa: trabajando en un ítem ── */}
          {activeItemId && trabajoActivo && (
            <>
              <button
                onClick={() => {
                  clearInterval(timerRef)
                  setTrabajoActivo(null)
                  setActiveItemId(null)
                  setFotoUrl(null)
                  setNotas('')
                  setElapsed(0)
                }}
                className="flex items-center gap-1.5 text-slate-500 hover:text-slate-800 text-sm font-medium transition-colors"
              >
                <ArrowLeft className="w-4 h-4" /> Volver a la lista
              </button>

              {/* Detalle del ítem activo */}
              {(() => {
                const item = allItems.find(i => i.id === activeItemId)
                return item ? (
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                    {item.seccion && (
                      <p className="text-blue-500 text-[10px] font-bold uppercase tracking-wider mb-1">{item.seccion}</p>
                    )}
                    <p className="text-blue-900 font-semibold text-sm">{item.observacion}</p>
                    <div className="flex items-center gap-2 mt-3 text-blue-700 text-xs font-semibold">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                      Trabajo en progreso · {fmt(elapsed)}
                    </div>
                  </div>
                ) : null
              })()}

              {/* Foto obligatoria */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Camera className="w-4 h-4 text-slate-500" />
                  <label className="text-sm font-bold text-slate-700">Foto del daño subsanado <span className="text-red-500">*</span></label>
                </div>
                <FotoUploader label="Toca para subir foto" onChange={setFotoUrl} />
              </div>

              {/* Observaciones del operario */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-slate-500" />
                  <label className="text-sm font-bold text-slate-700">Observación del operario</label>
                </div>
                <textarea
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  placeholder="Describe qué se hizo para subsanar este daño..."
                  rows={3}
                  className="w-full px-3 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 resize-none text-slate-800 placeholder:text-slate-400"
                />
              </div>

              {closeMut.isError && (
                <p className="text-red-500 text-sm font-medium bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                  {closeMut.error?.response?.data?.detail || 'Error al cerrar el trabajo'}
                </p>
              )}

              <button
                onClick={() => closeMut.mutate()}
                disabled={!fotoUrl || closeMut.isPending}
                className="w-full btn-primary justify-center py-3 text-base disabled:opacity-50"
              >
                {closeMut.isPending
                  ? <Loader2 className="w-5 h-5 animate-spin" />
                  : <CheckCircle2 className="w-5 h-5" />
                }
                {fotoUrl ? 'Confirmar Daño Subsanado' : 'Sube una foto para confirmar'}
              </button>
            </>
          )}

          {/* Cargando al iniciar trabajo */}
          {activeItemId && startMut.isPending && !trabajoActivo && (
            <div className="text-center py-6">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-2" />
              <p className="text-slate-500 text-sm">Iniciando trabajo...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────
export default function Pendientes() {
  const { user } = useAuth()
  const tipo     = user?.rol === 'operario_pintura' ? 'pintura' : 'repuesto'
  const [selected, setSelected] = useState(null)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['reprocesos', 'pendientes', tipo],
    queryFn: () => getReprocesos({ estado: 'pendiente' }),
    refetchInterval: 1000 * 60, // cada minuto
  })

  const reprocesos = data || []
  const Icon  = tipo === 'pintura' ? PaintBucket : Wrench
  const color = tipo === 'pintura' ? 'text-amber-500' : 'text-blue-600'
  const titulo = tipo === 'pintura' ? 'PINTURA' : 'REPUESTO'
  const accentBg = tipo === 'pintura' ? 'bg-amber-100 text-amber-800 border-amber-200' : 'bg-blue-100 text-blue-800 border-blue-200'

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-6">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center border shadow-sm bg-white border-slate-200`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">Pendientes — {titulo}</h1>
              <p className="text-slate-500 text-sm">{reprocesos.length} reproceso(s) asignado(s)</p>
            </div>
          </div>
          <button onClick={() => refetch()} className="p-2 rounded-lg border border-slate-200 text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition-colors text-xs font-medium">
            Actualizar
          </button>
        </div>

        {/* Lista */}
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : !reprocesos.length ? (
          <div className="bg-white border border-slate-200 rounded-2xl text-center py-16 shadow-sm">
            <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-3" />
            <p className="text-slate-900 font-bold text-lg">¡Sin daños pendientes!</p>
            <p className="text-slate-500 text-sm mt-1">Todo al día. 🎉</p>
          </div>
        ) : (
          <div className="space-y-3">
            {reprocesos.map((r) => (
              <div
                key={r.id}
                className="bg-white border border-slate-200 rounded-2xl shadow-sm hover:shadow-md hover:border-blue-300 transition-all cursor-pointer group"
                onClick={() => setSelected(r.id)}
              >
                <div className="p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="font-mono text-blue-600 text-xs font-bold tracking-widest mb-1">{r.vin}</p>
                      <p className="text-slate-900 font-bold text-base truncate">{r.vehiculos?.modelo || '—'}</p>
                      {/* Datos rápidos en la tarjeta */}
                      <div className="flex flex-wrap gap-x-4 gap-y-0.5 mt-1.5">
                        {r.vehiculos?.color && (
                          <span className="text-slate-500 text-xs flex items-center gap-1">
                            <Palette className="w-3 h-3" /> {r.vehiculos.color}
                          </span>
                        )}
                        {r.vehiculos?.concesionario && (
                          <span className="text-slate-500 text-xs flex items-center gap-1">
                            <Building2 className="w-3 h-3" /> {r.vehiculos.concesionario}
                          </span>
                        )}
                      </div>
                      {r.notas_cc && (
                        <p className="text-slate-400 text-xs mt-2 italic line-clamp-1">📋 "{r.notas_cc}"</p>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${accentBg}`}>
                        {tipo === 'pintura' ? 'Pintura' : 'Repuesto'}
                      </span>
                      <span className="text-slate-400 text-[10px]">{new Date(r.creado_en).toLocaleDateString('es-PE')}</span>
                    </div>
                  </div>
                </div>
                <div className="border-t border-slate-100 px-5 py-3 flex items-center justify-between">
                  <span className="text-slate-400 text-xs">Ver daños y subsanar</span>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selected && (
        <TrabajoModal
          reprocesoId={selected}
          tipo={tipo}
          onClose={() => setSelected(null)}
          onDone={() => { setSelected(null); refetch() }}
        />
      )}
    </div>
  )
}
