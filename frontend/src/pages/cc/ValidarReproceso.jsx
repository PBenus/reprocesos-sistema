import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  ArrowLeft, CheckCircle2, Loader2, Image as ImageIcon,
  PaintBucket, Wrench, User, Camera, FileText, Car, Building2, Palette, MapPin
} from 'lucide-react'
import Navbar from '../../components/Navbar'
import BottomNav from '../../components/BottomNav'
import { getReproceso, updateReproceso } from '../../api/reprocesos'
import client from '../../api/client'

// Obtiene los trabajos (con foto y operario) de un ítem específico
async function getTrabajosPorItem(tipo, itemId) {
  const tabla = tipo === 'pintura' ? 'trabajos_pintura' : 'trabajos_repuesto'
  const r = await client.get(`/items/${tipo}/${itemId}/trabajos`)
  return r.data
}

function FotoBox({ url, label }) {
  if (!url) return (
    <div className="flex flex-col items-center justify-center h-32 bg-slate-50 rounded-xl border-2 border-dashed border-slate-200 text-slate-400">
      <ImageIcon className="w-6 h-6 mb-1 opacity-40" />
      <span className="text-xs">Sin foto</span>
    </div>
  )
  return (
    <div>
      {label && <p className="text-xs text-slate-500 font-medium mb-1">{label}</p>}
      <a href={url} target="_blank" rel="noreferrer"
         className="block h-32 rounded-xl overflow-hidden border border-slate-200 hover:opacity-90 transition-opacity">
        <img src={url} alt="Evidencia" className="w-full h-full object-cover" />
      </a>
    </div>
  )
}

function ItemCard({ item, tipo, trabajos }) {
  const color  = tipo === 'pintura' ? 'text-amber-600' : 'text-blue-600'
  const badge  = tipo === 'pintura'
    ? 'bg-amber-100 text-amber-800 border-amber-200'
    : 'bg-blue-100 text-blue-800 border-blue-200'
  const Icon   = tipo === 'pintura' ? PaintBucket : Wrench

  // Trabajo de subsanación más reciente
  const trabajoCerrado = (trabajos || []).find(t => t.estado === 'cerrado')

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      {/* Header del ítem */}
      <div className="flex items-start gap-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
          tipo === 'pintura' ? 'bg-amber-50' : 'bg-blue-50'
        }`}>
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${badge}`}>
              {tipo === 'pintura' ? 'Pintura' : 'Repuesto'}
            </span>
            {item.seccion && (
              <span className="text-xs text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-full">
                {item.seccion}
              </span>
            )}
            <span className={`text-xs font-bold ml-auto ${
              item.estado === 'subsanado' ? 'text-green-600' : 'text-orange-500'
            }`}>
              {item.estado === 'subsanado' ? '✓ Subsanado' : item.estado}
            </span>
          </div>
          <p className="text-slate-900 font-semibold text-sm mt-1.5 leading-snug">{item.observacion}</p>
        </div>
      </div>

      {/* Comparación de fotos: Antes (CC) y Después (Operario) */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">📷 Foto Inicial (CC)</p>
          <FotoBox url={item.foto_url} />
        </div>
        <div>
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">✅ Foto Subsanado</p>
          <FotoBox url={trabajoCerrado?.foto_url} />
        </div>
      </div>

      {/* Info del operario que subsanó */}
      {trabajoCerrado && (
        <div className="bg-slate-50 border border-slate-100 rounded-xl p-3 space-y-1.5">
          {trabajoCerrado.nombre_operario && (
            <p className="text-xs text-slate-600 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-400" />
              <strong>Subsanado por:</strong> {trabajoCerrado.nombre_operario}
            </p>
          )}
          {trabajoCerrado.notas && (
            <p className="text-xs text-slate-600 flex items-start gap-1.5">
              <FileText className="w-3.5 h-3.5 text-slate-400 mt-0.5 flex-shrink-0" />
              <span><strong>Observación:</strong> {trabajoCerrado.notas}</span>
            </p>
          )}
          {trabajoCerrado.cerrado_en && (
            <p className="text-xs text-slate-400">
              Cerrado: {new Date(trabajoCerrado.cerrado_en).toLocaleString('es-PE')}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export default function ValidarReproceso() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [success, setSuccess] = useState(false)

  const { data: reproceso, isLoading } = useQuery({
    queryKey: ['reproceso', id],
    queryFn: () => getReproceso(id),
  })

  // Traer los trabajos de cada ítem de pintura
  const { data: trabajosPintura = [] } = useQuery({
    queryKey: ['trabajos-detalle', id, 'pintura'],
    queryFn: async () => {
      if (!reproceso?.items_pintura?.length) return []
      const results = await Promise.all(
        reproceso.items_pintura.map(item =>
          client.get(`/trabajos/pintura/item/${item.id}`).then(r => r.data).catch(() => [])
        )
      )
      return results.flat()
    },
    enabled: !!reproceso?.items_pintura?.length,
  })

  // Traer los trabajos de cada ítem de repuesto
  const { data: trabajosRepuesto = [] } = useQuery({
    queryKey: ['trabajos-detalle', id, 'repuesto'],
    queryFn: async () => {
      if (!reproceso?.items_repuesto?.length) return []
      const results = await Promise.all(
        reproceso.items_repuesto.map(item =>
          client.get(`/trabajos/repuesto/item/${item.id}`).then(r => r.data).catch(() => [])
        )
      )
      return results.flat()
    },
    enabled: !!reproceso?.items_repuesto?.length,
  })

  const mutation = useMutation({
    mutationFn: () => updateReproceso(id, { estado: 'cerrado' }),
    onSuccess: () => {
      setSuccess(true)
      setTimeout(() => navigate('/cc/validar'), 2000)
    }
  })

  if (isLoading) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
    </div>
  )

  if (success) return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center animate-slide-up bg-white p-10 rounded-2xl shadow-lg border border-slate-200">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">¡Reproceso Validado y Cerrado!</h2>
        <p className="text-slate-500 text-sm mt-1">Redirigiendo...</p>
      </div>
    </div>
  )

  const v = reproceso?.vehiculos
  const totalItems = (reproceso?.items_pintura?.length || 0) + (reproceso?.items_repuesto?.length || 0)
  const subsanados = [
    ...(reproceso?.items_pintura || []),
    ...(reproceso?.items_repuesto || [])
  ].filter(i => i.estado === 'subsanado').length

  return (
    <div className="min-h-screen bg-slate-50 pb-24">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-5 animate-fade-in">

        <button onClick={() => navigate('/cc/validar')}
                className="flex items-center gap-2 text-slate-500 hover:text-slate-800 text-sm font-medium transition-colors">
          <ArrowLeft className="w-4 h-4" /> Volver a Para Validar
        </button>

        {/* Cabecera del reproceso */}
        {reproceso && (
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <p className="font-mono text-blue-600 text-xs font-bold tracking-widest">{reproceso.vin}</p>
                <h1 className="text-xl font-bold text-slate-900 mt-0.5">{v?.modelo || '—'}</h1>
                {reproceso.nombre_creador && (
                  <p className="text-slate-500 text-sm mt-1 flex items-center gap-1">
                    <User className="w-3.5 h-3.5" /> Reproceso creado por: <strong>{reproceso.nombre_creador}</strong>
                  </p>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <span className="bg-amber-100 text-amber-800 border border-amber-200 px-3 py-1 rounded-full text-xs font-bold">
                  Por Validar
                </span>
                <p className="text-slate-400 text-xs mt-2">{subsanados}/{totalItems} ítems subsanados</p>
              </div>
            </div>

            {/* Datos del vehículo */}
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 bg-slate-50 rounded-xl p-3 border border-slate-100">
              {v?.color && <p className="text-xs text-slate-600 flex items-center gap-1.5"><Palette className="w-3.5 h-3.5 text-slate-400" /><strong>Color:</strong> {v.color}</p>}
              {v?.concesionario && <p className="text-xs text-slate-600 flex items-center gap-1.5"><Building2 className="w-3.5 h-3.5 text-slate-400" /><strong>Concesionario:</strong> {v.concesionario}</p>}
              {v?.marca && <p className="text-xs text-slate-600 flex items-center gap-1.5"><Car className="w-3.5 h-3.5 text-slate-400" /><strong>Marca:</strong> {v.marca}</p>}
              {v?.taller && <p className="text-xs text-slate-600 flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-slate-400" /><strong>Taller:</strong> {v.taller}</p>}
            </div>

            {reproceso.notas_cc && (
              <div className="mt-3 p-3 bg-amber-50 border border-amber-100 rounded-xl">
                <p className="text-xs font-bold text-amber-600 uppercase tracking-wider mb-1">📋 Notas CC</p>
                <p className="text-slate-800 text-sm">{reproceso.notas_cc}</p>
              </div>
            )}
          </div>
        )}

        {/* Ítems de Pintura */}
        {reproceso?.items_pintura?.map(item => (
          <ItemCard
            key={item.id}
            item={item}
            tipo="pintura"
            trabajos={trabajosPintura.filter(t => t.item_id === item.id)}
          />
        ))}

        {/* Ítems de Repuesto */}
        {reproceso?.items_repuesto?.map(item => (
          <ItemCard
            key={item.id}
            item={item}
            tipo="repuesto"
            trabajos={trabajosRepuesto.filter(t => t.item_id === item.id)}
          />
        ))}

        {/* Botón de cierre */}
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="w-full btn-primary py-4 justify-center text-base rounded-2xl mt-2"
        >
          {mutation.isPending
            ? <Loader2 className="w-5 h-5 animate-spin" />
            : <CheckCircle2 className="w-5 h-5" />
          }
          Aprobar y Cerrar Reproceso
        </button>

      </div>
      <BottomNav />
    </div>
  )
}
