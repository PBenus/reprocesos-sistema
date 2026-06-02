import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowLeft, PaintBucket, Wrench, Plus, AlertCircle, Loader2,
  RefreshCw, CheckCircle2, Clock, ChevronDown, ChevronUp,
  Building2, Calendar, Image as ImageIcon, User, FileText
} from 'lucide-react'
import Navbar from '../../components/Navbar'
import BottomNav from '../../components/BottomNav'
import { getVehiculo } from '../../api/vehiculos'
import { getReprocesos } from '../../api/reprocesos'

// ─── Tabla daños pintura (eSUM) ────────────────────────────────────────────
function DanosPintura({ danos }) {
  if (!danos?.length) return <p className="text-slate-500 text-sm py-4">Sin daños de pintura registrados.</p>
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-200">
            <th className="py-2 pr-4 font-medium">Fecha</th>
            <th className="py-2 pr-4 font-medium">Sección</th>
            <th className="py-2 pr-4 font-medium">Validación</th>
            <th className="py-2 pr-4 font-medium">Paños</th>
            <th className="py-2 font-medium">Colaborador</th>
          </tr>
        </thead>
        <tbody>
          {danos.map((d, i) => (
            <tr key={i} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
              <td className="py-2 pr-4 text-slate-500 text-xs whitespace-nowrap">
                {d.fecha_hora ? new Date(d.fecha_hora).toLocaleDateString('es-PE') : '—'}
              </td>
              <td className="py-2 pr-4 text-slate-800">{d.seccion || '—'}</td>
              <td className="py-2 pr-4">
                <span className={`badge text-xs ${
                  d.validacion === 'PASA' ? 'badge-green' :
                  d.validacion === 'PAÑOS' ? 'badge-yellow' :
                  d.validacion === 'PULIR' ? 'badge-blue' : 'badge-red'
                }`}>{d.validacion || '—'}</span>
              </td>
              <td className="py-2 pr-4 text-slate-800 text-center">{d.num_panos || '—'}</td>
              <td className="py-2 text-slate-600">{d.colaborador || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Tabla daños repuesto (eSUM) ───────────────────────────────────────────
function DanosRepuesto({ danos }) {
  if (!danos?.length) return <p className="text-slate-500 text-sm py-4">Sin daños de repuesto registrados.</p>
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-200">
            <th className="py-2 pr-4 font-medium">Sección</th>
            <th className="py-2 pr-4 font-medium">Diagnóstico</th>
            <th className="py-2 pr-4 font-medium">Validado por</th>
            <th className="py-2 font-medium">Fecha Reg.</th>
          </tr>
        </thead>
        <tbody>
          {danos.map((d, i) => (
            <tr key={i} className="border-b border-slate-100 hover:bg-slate-50 transition-colors">
              <td className="py-2 pr-4 text-slate-800">{d.seccion || '—'}</td>
              <td className="py-2 pr-4 text-slate-600 max-w-xs truncate" title={d.diagnostico}>{d.diagnostico || '—'}</td>
              <td className="py-2 pr-4 text-slate-600">{d.validado_por || '—'}</td>
              <td className="py-2 text-slate-500 text-xs whitespace-nowrap">{d.fecha_registro || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Badge de estado de reproceso ─────────────────────────────────────────
function EstadoBadge({ estado }) {
  const map = {
    pendiente:   { cls: 'bg-orange-100 text-orange-700 border-orange-200',  label: '⏳ En proceso' },
    por_validar: { cls: 'bg-amber-100 text-amber-700 border-amber-200',     label: '🔍 Por validar' },
    cerrado:     { cls: 'bg-green-100 text-green-700 border-green-200',     label: '✅ Cerrado' },
  }
  const { cls, label } = map[estado] || { cls: 'bg-slate-100 text-slate-600 border-slate-200', label: estado }
  return <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${cls}`}>{label}</span>
}

// ─── Ítem de reproceso expandible ─────────────────────────────────────────
function ItemReproceso({ item, tipo }) {
  const [open, setOpen] = useState(false)
  const Icon = tipo === 'pintura' ? PaintBucket : Wrench
  const color = tipo === 'pintura' ? 'text-amber-600 bg-amber-50 border-amber-200' : 'text-blue-600 bg-blue-50 border-blue-200'
  const estadoItem = {
    pendiente:   { cls: 'text-orange-500', label: 'Pendiente' },
    en_proceso:  { cls: 'text-blue-500',   label: 'En proceso' },
    subsanado:   { cls: 'text-green-600',  label: '✓ Subsanado' },
  }
  const { cls, label } = estadoItem[item.estado] || { cls: 'text-slate-500', label: item.estado }

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-white hover:bg-slate-50 transition-colors text-left"
      >
        <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 border ${color}`}>
          <Icon className="w-3.5 h-3.5" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-800 truncate">{item.observacion}</p>
          {item.seccion && <p className="text-xs text-slate-400">{item.seccion}</p>}
        </div>
        <span className={`text-xs font-semibold flex-shrink-0 ${cls}`}>{label}</span>
        {open ? <ChevronUp className="w-4 h-4 text-slate-400 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-slate-400 flex-shrink-0" />}
      </button>

      {open && (
        <div className="border-t border-slate-100 bg-slate-50 p-4 space-y-3">
          {/* Fotos antes/después */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">📷 Foto CC (Antes)</p>
              {item.foto_url
                ? <a href={item.foto_url} target="_blank" rel="noreferrer" className="block h-28 rounded-lg overflow-hidden border border-slate-200 hover:opacity-90 transition-opacity">
                    <img src={item.foto_url} alt="Antes" className="w-full h-full object-cover" />
                  </a>
                : <div className="h-28 rounded-lg border-2 border-dashed border-slate-200 flex items-center justify-center">
                    <p className="text-xs text-slate-400">Sin foto</p>
                  </div>
              }
            </div>
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">✅ Foto Subsanado</p>
              {item.trabajo_foto
                ? <a href={item.trabajo_foto} target="_blank" rel="noreferrer" className="block h-28 rounded-lg overflow-hidden border border-slate-200 hover:opacity-90 transition-opacity">
                    <img src={item.trabajo_foto} alt="Después" className="w-full h-full object-cover" />
                  </a>
                : <div className="h-28 rounded-lg border-2 border-dashed border-slate-200 flex items-center justify-center">
                    <p className="text-xs text-slate-400">{item.estado === 'subsanado' ? 'Sin foto' : 'Pendiente'}</p>
                  </div>
              }
            </div>
          </div>
          {/* Info del operario */}
          {(item.nombre_operario || item.trabajo_notas || item.trabajo_cerrado_en) && (
            <div className="bg-white rounded-lg border border-slate-200 p-3 space-y-1.5">
              {item.nombre_operario && (
                <p className="text-xs text-slate-600 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-slate-400" />
                  <strong>Operario:</strong> {item.nombre_operario}
                </p>
              )}
              {item.trabajo_notas && (
                <p className="text-xs text-slate-600 flex items-start gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-slate-400 mt-0.5 flex-shrink-0" />
                  <span><strong>Observación:</strong> {item.trabajo_notas}</span>
                </p>
              )}
              {item.trabajo_cerrado_en && (
                <p className="text-xs text-slate-400">
                  Cerrado: {new Date(item.trabajo_cerrado_en).toLocaleString('es-PE')}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Card de un reproceso completo ────────────────────────────────────────
function ReprocesCard({ rep }) {
  const [open, setOpen] = useState(true)
  const totalItems = (rep.items_pintura?.length || 0) + (rep.items_repuesto?.length || 0)
  const subsanados = [
    ...(rep.items_pintura || []),
    ...(rep.items_repuesto || [])
  ].filter(i => i.estado === 'subsanado').length

  return (
    <div className="border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
      {/* Header del reproceso */}
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between gap-4 px-5 py-4 bg-white hover:bg-slate-50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-indigo-50 rounded-xl flex items-center justify-center border border-indigo-200">
            <RefreshCw className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-900">
              Reproceso #{rep.id?.slice(-6).toUpperCase()}
            </p>
            <p className="text-xs text-slate-400 flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {new Date(rep.creado_en).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' })}
              {rep.nombre_creador && <> · <User className="w-3 h-3" />{rep.nombre_creador}</>}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <EstadoBadge estado={rep.estado} />
          <span className="text-xs text-slate-400">{subsanados}/{totalItems}</span>
          {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      {open && (
        <div className="border-t border-slate-100 bg-slate-50 p-4 space-y-2">
          {rep.notas_cc && (
            <div className="bg-amber-50 border border-amber-100 rounded-xl px-3 py-2 mb-3">
              <p className="text-xs font-bold text-amber-600 mb-0.5">📋 Notas CC</p>
              <p className="text-xs text-slate-700">{rep.notas_cc}</p>
            </div>
          )}
          {(rep.items_pintura || []).map(item => (
            <ItemReproceso key={item.id} item={item} tipo="pintura" />
          ))}
          {(rep.items_repuesto || []).map(item => (
            <ItemReproceso key={item.id} item={item} tipo="repuesto" />
          ))}
          {totalItems === 0 && (
            <p className="text-slate-400 text-sm text-center py-2">Sin ítems registrados</p>
          )}
        </div>
      )}
    </div>
  )
}

// ─── Pestaña Reprocesos ───────────────────────────────────────────────────
function TabReprocesos({ vin, onNuevoReproceso }) {
  const { data: reprocesos = [], isLoading } = useQuery({
    queryKey: ['reprocesos', 'por-vin', vin],
    queryFn: () => getReprocesos({ vin }),
  })

  if (isLoading) return (
    <div className="flex justify-center py-8">
      <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
    </div>
  )

  if (reprocesos.length === 0) return (
    <div className="text-center py-10 space-y-3">
      <div className="w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center mx-auto">
        <RefreshCw className="w-6 h-6 text-indigo-400" />
      </div>
      <p className="text-slate-500 text-sm">No hay reprocesos registrados para este vehículo.</p>
      <button onClick={onNuevoReproceso} className="btn-primary text-sm px-4 py-2">
        <Plus className="w-4 h-4" /> Crear primer reproceso
      </button>
    </div>
  )

  return (
    <div className="space-y-3">
      {reprocesos.map(rep => (
        <ReprocesCard key={rep.id} rep={rep} />
      ))}
    </div>
  )
}

// ─── Página principal ─────────────────────────────────────────────────────
export default function VehicleDetail() {
  const { vin }    = useParams()
  const navigate   = useNavigate()
  const [tab, setTab] = useState('reprocesos')

  const { data: vehiculo, isLoading, error } = useQuery({
    queryKey: ['vehiculo', vin],
    queryFn: () => getVehiculo(vin),
  })

  if (isLoading) return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    </div>
  )

  if (error || !vehiculo) return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 pt-8">
        <div className="card flex items-center gap-3 text-red-600">
          <AlertCircle /> Error al cargar el vehículo
        </div>
      </div>
    </div>
  )

  const TABS = [
    { key: 'reprocesos', label: 'Reprocesos', icon: RefreshCw,   color: 'indigo' },
    { key: 'pintura',    label: 'Daños Pintura', icon: PaintBucket, color: 'amber' },
    { key: 'repuesto',   label: 'Daños Repuesto', icon: Wrench,    color: 'blue' },
  ]

  return (
    <div className="min-h-screen bg-slate-50 pb-24">
      <Navbar />
      <div className="max-w-5xl mx-auto px-4 py-6 space-y-5 animate-fade-in">

        <button onClick={() => navigate(-1)} className="btn-secondary text-sm">
          <ArrowLeft className="w-4 h-4" /> Volver
        </button>

        {/* Header vehículo */}
        <div className="card">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div>
              <p className="font-mono text-blue-600 text-sm font-bold tracking-widest mb-1">{vehiculo.vin}</p>
              <h1 className="text-xl font-bold text-slate-900">{vehiculo.modelo}</h1>
              <p className="text-slate-500">{vehiculo.marca} · {vehiculo.color}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className={`badge ${vehiculo.estado === 'EN PROCESO' ? 'badge-green' : 'badge-yellow'}`}>
                {vehiculo.estado}
              </span>
              <span className="badge-blue">{vehiculo.proceso}</span>
              {vehiculo.dias_transcurridos !== null && (
                <span className={`badge ${
                  vehiculo.dias_transcurridos <= 3 ? 'badge-green' :
                  vehiculo.dias_transcurridos <= 7 ? 'badge-yellow' : 'badge-red'
                }`}>
                  {vehiculo.dias_transcurridos} días
                </span>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-5 pt-4 border-t border-slate-200">
            <div><p className="text-slate-400 text-xs uppercase tracking-wide">Concesionario</p><p className="text-slate-800 font-medium text-sm mt-0.5">{vehiculo.concesionario || '—'}</p></div>
            <div><p className="text-slate-400 text-xs uppercase tracking-wide">F. Ingreso</p><p className="text-slate-800 font-medium text-sm mt-0.5">{vehiculo.fecha_ingreso_flujo || '—'}</p></div>
            <div><p className="text-slate-400 text-xs uppercase tracking-wide">F. Planificada</p><p className="text-slate-800 font-medium text-sm mt-0.5">{vehiculo.fecha_planificada || '—'}</p></div>
          </div>
        </div>

        {/* Tabs */}
        <div className="card">
          <div className="flex gap-1 mb-5 border-b border-slate-200 pb-3 overflow-x-auto">
            {TABS.map(({ key, label, icon: Icon, color }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                  tab === key
                    ? `bg-${color}-50 text-${color}-700 border border-${color}-200`
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
                {key === 'pintura'  && <span className="bg-white border border-slate-200 text-slate-600 px-2 rounded-full text-xs ml-1">{vehiculo.danos_pintura?.length || 0}</span>}
                {key === 'repuesto' && <span className="bg-white border border-slate-200 text-slate-600 px-2 rounded-full text-xs ml-1">{vehiculo.danos_repuesto?.length || 0}</span>}
              </button>
            ))}
          </div>

          {tab === 'reprocesos' && (
            <TabReprocesos vin={vin} onNuevoReproceso={() => navigate(`/cc/reproceso/nuevo/${vin}`)} />
          )}
          {tab === 'pintura'  && <DanosPintura  danos={vehiculo.danos_pintura} />}
          {tab === 'repuesto' && <DanosRepuesto danos={vehiculo.danos_repuesto} />}
        </div>

        {/* Botón nuevo reproceso */}
        <div className="flex justify-end">
          <button
            onClick={() => navigate(`/cc/reproceso/nuevo/${vin}`)}
            className="btn-primary px-6 py-3 text-base"
          >
            <Plus className="w-5 h-5" /> Iniciar Reproceso
          </button>
        </div>

      </div>
      <BottomNav />
    </div>
  )
}
