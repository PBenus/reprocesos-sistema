import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ArrowLeft, Plus, Trash2, PaintBucket, Wrench, Loader2, CheckCircle2 } from 'lucide-react'
import Navbar from '../../components/Navbar'
import BottomNav from '../../components/BottomNav'
import FotoUploader from '../../components/FotoUploader'
import { getVehiculo } from '../../api/vehiculos'
import { createReproceso } from '../../api/reprocesos'

const SECCIONES = [
  'Capot','Techo','Maletero','Parachoque delantero','Parachoque posterior',
  'Puerta Del LH','Puerta Del RH','Puerta Pos LH','Puerta Pos RH',
  'Guardafango Del LH','Guardafango Del RH','Lateral LH','Lateral RH',
  'Espejo LH','Espejo RH','Parabrisas','Luna posterior','Observaciones','Otro',
]

function ItemRow({ item, onChange, onDelete, tipo }) {
  return (
    <div className="flex gap-2 items-start bg-white rounded-xl p-4 border border-slate-200 shadow-sm group animate-fade-in">
      <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${tipo === 'pintura' ? 'bg-amber-400' : 'bg-blue-500'}`} />
      <div className="flex-1 space-y-3">
        <div className={`grid grid-cols-1 ${tipo === 'repuesto' ? 'sm:grid-cols-2' : ''} gap-3`}>
          {tipo === 'repuesto' && (
            <div>
              <label className="text-slate-600 font-medium text-xs mb-1.5 block">Sección / Pieza</label>
              <select
                value={item.seccion}
                onChange={(e) => onChange({ ...item, seccion: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800"
              >
                <option value="">Selecciona sección...</option>
                {SECCIONES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          )}
          <div>
            <label className="text-slate-600 font-medium text-xs mb-1.5 block">Observación</label>
            <textarea
              value={item.observacion}
              onChange={(e) => onChange({ ...item, observacion: e.target.value })}
              placeholder="Describe el daño..."
              rows={2}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 resize-none"
            />
          </div>
        </div>
        <div>
          <FotoUploader 
            label="Foto de evidencia (opcional)" 
            onChange={(url) => onChange({ ...item, foto_url: url })} 
          />
        </div>
      </div>
      <button
        type="button"
        onClick={onDelete}
        className="text-slate-400 hover:text-red-500 transition-colors mt-1 p-1 flex-shrink-0"
      >
        <Trash2 className="w-5 h-5" />
      </button>
    </div>
  )
}

let _id = 0
const newItem = () => ({ _id: ++_id, seccion: '', observacion: '', foto_url: null })

export default function IniciarReproceso() {
  const { vin }  = useParams()
  const navigate = useNavigate()

  const [notas, setNotas]             = useState('')
  const [itemsPintura, setItemsP]     = useState([newItem()])
  const [itemsRepuesto, setItemsR]    = useState([])
  const [success, setSuccess]         = useState(false)

  const { data: vehiculo, isLoading } = useQuery({
    queryKey: ['vehiculo', vin],
    queryFn: () => getVehiculo(vin),
  })

  const mutation = useMutation({
    mutationFn: (payload) => createReproceso(payload),
    onSuccess: () => { setSuccess(true); setTimeout(() => navigate('/cc/dashboard'), 2000) },
  })

  const updateP = (idx, val) => setItemsP((p) => p.map((it, i) => i === idx ? val : it))
  const updateR = (idx, val) => setItemsR((p) => p.map((it, i) => i === idx ? val : it))

  const handleSubmit = (e) => {
    e.preventDefault()
    // Pintura no requiere seccion
    const pintura  = itemsPintura.filter((i) => i.observacion)
    // Repuesto sí requiere seccion
    const repuesto = itemsRepuesto.filter((i) => i.seccion && i.observacion)

    if (!pintura.length && !repuesto.length) {
      alert('Agrega al menos un ítem de daño correctamente (Observación requerida. Para repuestos, también Sección).')
      return
    }
    mutation.mutate({
      vin,
      notas_cc: notas,
      items_pintura: pintura.map(({ observacion, foto_url }) => ({ seccion: null, observacion, foto_url })),
      items_repuesto: repuesto.map(({ seccion, observacion, foto_url }) => ({ seccion, observacion, foto_url })),
    })
  }

  if (success) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center animate-slide-up bg-white p-8 rounded-xl shadow-sm border border-slate-200">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">¡Reproceso creado!</h2>
        <p className="text-slate-500 mt-1">Redirigiendo al dashboard...</p>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-6 animate-fade-in">

        <button onClick={() => navigate(`/cc/vehiculo/${vin}`)} className="btn-secondary text-sm">
          <ArrowLeft className="w-4 h-4" /> Volver a ficha
        </button>

        {/* Info del vehículo */}
        {vehiculo && (
          <div className="bg-white border border-slate-200 p-4 rounded-lg shadow-sm flex items-center gap-4">
            <div className="flex-1">
              <p className="font-mono text-blue-600 text-xs font-bold tracking-widest">{vehiculo.vin}</p>
              <p className="text-slate-900 font-bold text-lg">{vehiculo.modelo}</p>
              <p className="text-slate-500 text-sm font-medium">{vehiculo.proceso}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">

          {/* Notas generales */}
          <div className="bg-white border border-slate-200 p-4 rounded-lg shadow-sm">
            <h2 className="text-slate-800 font-bold mb-3 text-[15px]">Notas generales de CC</h2>
            <textarea
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
              placeholder="Observaciones generales del control de calidad..."
              rows={3}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 resize-none"
            />
          </div>

          {/* Ítems de PINTURA */}
          <div className="bg-white border border-slate-200 p-4 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
              <h2 className="text-slate-800 font-bold flex items-center gap-2 text-[15px]">
                <PaintBucket className="w-5 h-5 text-amber-500" /> Daños de PINTURA
                <span className="bg-amber-100 text-amber-800 border border-amber-200 px-2 rounded-full text-xs font-medium">{itemsPintura.length}</span>
              </h2>
              <button
                type="button"
                onClick={() => setItemsP((p) => [...p, newItem()])}
                className="flex items-center gap-1.5 text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors"
              >
                <Plus className="w-4 h-4" /> Agregar
              </button>
            </div>
            <div className="space-y-3">
              {itemsPintura.map((item, i) => (
                <ItemRow key={item._id} item={item} tipo="pintura"
                  onChange={(v) => updateP(i, v)}
                  onDelete={() => setItemsP((p) => p.filter((_, j) => j !== i))}
                />
              ))}
              {!itemsPintura.length && <p className="text-slate-500 text-sm">Sin ítems de pintura</p>}
            </div>
          </div>

          {/* Ítems de REPUESTO */}
          <div className="bg-white border border-slate-200 p-4 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
              <h2 className="text-slate-800 font-bold flex items-center gap-2 text-[15px]">
                <Wrench className="w-5 h-5 text-blue-500" /> Daños de REPUESTO
                <span className="bg-blue-100 text-blue-800 border border-blue-200 px-2 rounded-full text-xs font-medium">{itemsRepuesto.length}</span>
              </h2>
              <button
                type="button"
                onClick={() => setItemsR((p) => [...p, newItem()])}
                className="flex items-center gap-1.5 text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors"
              >
                <Plus className="w-4 h-4" /> Agregar
              </button>
            </div>
            <div className="space-y-3">
              {itemsRepuesto.map((item, i) => (
                <ItemRow key={item._id} item={item} tipo="repuesto"
                  onChange={(v) => updateR(i, v)}
                  onDelete={() => setItemsR((p) => p.filter((_, j) => j !== i))}
                />
              ))}
              {!itemsRepuesto.length && <p className="text-slate-500 text-sm">Sin ítems de repuesto</p>}
            </div>
          </div>

          {/* Error */}
          {mutation.isError && (
            <div className="text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
              {mutation.error?.response?.data?.detail || 'Error al crear el reproceso'}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={mutation.isPending}
            className="w-full btn-primary py-3 text-base justify-center mt-6"
          >
            {mutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle2 className="w-5 h-5" />}
            {mutation.isPending ? 'Creando reproceso...' : 'Confirmar Reproceso'}
          </button>
        </form>
      </div>
      <BottomNav />
    </div>
  )
}
