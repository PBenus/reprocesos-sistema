/**
 * TrabajoModal.jsx — Modal completo para gestionar un reproceso desde el operario
 */
import { useState, useEffect, useRef } from 'react'
import {
  X, Play, Square, Clock, CheckCircle2, Camera,
  Loader2, AlertCircle, Wrench, FileText
} from 'lucide-react'
import FotoUploader from './FotoUploader'
import { iniciarTrabajoP, cerrarTrabajoP, iniciarTrabajoR, cerrarTrabajoR } from '../api/trabajos'

/* ── Timer en tiempo real ────────────────────────────────────────── */
function LiveTimer({ startTime }) {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const calc = () => {
      const start = new Date(startTime).getTime()
      setElapsed(Math.floor((Date.now() - start) / 1000))
    }
    calc()
    const interval = setInterval(calc, 1000)
    return () => clearInterval(interval)
  }, [startTime])

  const hours = Math.floor(elapsed / 3600)
  const mins = Math.floor((elapsed % 3600) / 60)
  const secs = elapsed % 60

  const fmt = (n) => String(n).padStart(2, '0')
  const color = elapsed > 3600 * 4 ? 'text-danger' : elapsed > 3600 ? 'text-warning' : 'text-success'

  return (
    <div className={`font-mono text-3xl font-bold ${color} tabular-nums`}>
      {fmt(hours)}:{fmt(mins)}:{fmt(secs)}
    </div>
  )
}

/* ── TrabajoModal ─────────────────────────────────────────────────── */
export default function TrabajoModal({ reproceso, tipo, onClose, onSuccess }) {
  // tipo: 'pintura' | 'repuesto'
  const [step, setStep] = useState('inicio') // inicio | trabajando | cerrando | done
  const [trabajoId, setTrabajoId] = useState(null)
  const [abiertoen, setAbiertoen] = useState(null)
  const [selectedItemId, setSelectedItemId] = useState(null)
  const [subsanados, setSubsanados] = useState([])
  const [fotoUrl, setFotoUrl] = useState(null)
  const [notas, setNotas] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const items = tipo === 'pintura'
    ? (reproceso?.items_pintura || [])
    : (reproceso?.items_repuesto || [])

  const pendientes = items.filter((i) => i.estado === 'PENDIENTE' || !i.cerrado_en)

  /* ── Iniciar trabajo ─────────────────────────────────────────── */
  const handleIniciar = async () => {
    if (!selectedItemId) {
      setError('Selecciona al menos un ítem para trabajar')
      return
    }
    setError('')
    setIsLoading(true)
    try {
      const fn = tipo === 'pintura' ? iniciarTrabajoP : iniciarTrabajoR
      const data = await fn(selectedItemId)
      setTrabajoId(data.id)
      setAbiertoen(data.abierto_en || new Date().toISOString())
      setStep('trabajando')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Error al iniciar el trabajo')
    } finally {
      setIsLoading(false)
    }
  }

  /* ── Cerrar trabajo ──────────────────────────────────────────── */
  const handleCerrar = async () => {
    if (subsanados.length === 0) {
      setError('Marca al menos un daño como subsanado')
      return
    }
    setError('')
    setIsLoading(true)
    try {
      const fn = tipo === 'pintura' ? cerrarTrabajoP : cerrarTrabajoR
      await fn(trabajoId, {
        items_subsanados: subsanados,
        foto_cierre_url: fotoUrl || null,
        notas: notas.trim() || null,
      })
      setStep('done')
      setTimeout(() => {
        onSuccess?.()
        onClose()
      }, 2000)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Error al cerrar el trabajo')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleSubsanado = (id) => {
    setSubsanados((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  /* ── Render ──────────────────────────────────────────────────── */
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-lg bg-surface-800 rounded-2xl border border-surface-600 shadow-[0_20px_60px_rgba(0,0,0,0.7)] animate-slide-up">

        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-surface-700">
          <div>
            <h2 className="font-bold text-white text-lg flex items-center gap-2">
              <Wrench className="w-5 h-5 text-brand-400" />
              {tipo === 'pintura' ? 'Trabajo de Pintura' : 'Trabajo de Repuesto'}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              VIN: <code className="text-brand-400 font-mono">{reproceso?.vin}</code>
              {reproceso?.modelo && ` · ${reproceso.modelo}`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-surface-700 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-5 max-h-[70vh] overflow-y-auto">

          {/* STEP: inicio */}
          {step === 'inicio' && (
            <>
              <div>
                <p className="text-sm text-slate-400 mb-3">
                  Selecciona el ítem en el que vas a trabajar:
                </p>
                <div className="space-y-2">
                  {pendientes.map((item) => (
                    <label
                      key={item.id}
                      className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer border transition-all ${
                        selectedItemId === item.id
                          ? 'border-brand-500 bg-brand-900/30'
                          : 'border-surface-600 hover:border-surface-500 bg-surface-900/40'
                      }`}
                    >
                      <input
                        type="radio"
                        name="item_seleccionado"
                        value={item.id}
                        checked={selectedItemId === item.id}
                        onChange={() => setSelectedItemId(item.id)}
                        className="mt-0.5 accent-brand-500"
                      />
                      <div>
                        <p className="text-sm font-semibold text-slate-200">{item.seccion}</p>
                        {item.observacion && (
                          <p className="text-xs text-slate-500 mt-0.5">{item.observacion}</p>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 text-xs text-danger">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" /> {error}
                </div>
              )}

              <button
                onClick={handleIniciar}
                disabled={isLoading}
                className="btn-success w-full py-3 font-semibold"
              >
                {isLoading
                  ? <><Loader2 className="w-4 h-4 animate-spin" /> Iniciando...</>
                  : <><Play className="w-4 h-4" /> Iniciar Trabajo</>
                }
              </button>
            </>
          )}

          {/* STEP: trabajando */}
          {step === 'trabajando' && (
            <>
              <div className="text-center py-2">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Tiempo transcurrido</p>
                {abiertoen && <LiveTimer startTime={abiertoen} />}
                <div className="flex items-center justify-center gap-1.5 mt-2">
                  <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                  <span className="text-xs text-success font-medium">Trabajo en curso</span>
                </div>
              </div>

              <div className="divider" />

              <button
                onClick={() => setStep('cerrando')}
                className="btn-danger w-full py-3 font-semibold"
              >
                <Square className="w-4 h-4" />
                Registrar Cierre
              </button>
            </>
          )}

          {/* STEP: cerrando */}
          {step === 'cerrando' && (
            <>
              <div>
                <p className="label">¿Qué daños subsanaste?</p>
                <div className="space-y-2">
                  {pendientes.map((item) => (
                    <label
                      key={item.id}
                      className="flex items-center gap-3 p-3 rounded-xl cursor-pointer border border-surface-600 hover:border-surface-500 bg-surface-900/40 transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={subsanados.includes(item.id)}
                        onChange={() => toggleSubsanado(item.id)}
                        className="w-4 h-4 accent-success"
                      />
                      <div>
                        <p className="text-sm font-medium text-slate-200">{item.seccion}</p>
                        {item.observacion && (
                          <p className="text-xs text-slate-500">{item.observacion}</p>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* Foto de cierre */}
              <FotoUploader
                label="Foto del daño subsanado"
                onChange={setFotoUrl}
              />

              {/* Notas */}
              <div>
                <label className="label">Notas (opcional)</label>
                <textarea
                  rows={2}
                  placeholder="Observaciones del trabajo realizado..."
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  className="input resize-none text-sm"
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 text-xs text-danger">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" /> {error}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep('trabajando')}
                  className="btn-secondary flex-1"
                  disabled={isLoading}
                >
                  Volver
                </button>
                <button
                  type="button"
                  onClick={handleCerrar}
                  disabled={isLoading}
                  className="btn-success flex-1 font-semibold"
                >
                  {isLoading
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Cerrando...</>
                    : <><CheckCircle2 className="w-4 h-4" /> Confirmar Cierre</>
                  }
                </button>
              </div>
            </>
          )}

          {/* STEP: done */}
          {step === 'done' && (
            <div className="text-center py-8 animate-slide-up">
              <div className="w-16 h-16 rounded-full bg-success/20 border-2 border-success/40 flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-8 h-8 text-success" />
              </div>
              <h3 className="text-lg font-bold text-white mb-1">¡Trabajo Cerrado!</h3>
              <p className="text-sm text-slate-400">El trabajo ha sido registrado exitosamente.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
