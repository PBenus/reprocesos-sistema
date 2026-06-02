import { useState, useRef } from 'react'
import { Camera, X, Loader2, Upload } from 'lucide-react'
import { uploadFoto } from '../api/fotos'

export default function FotoUploader({ onChange, label = 'Foto del trabajo' }) {
  const [preview, setPreview]   = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState('')
  const fileRef = useRef()

  const handleFile = async (file) => {
    if (!file) return
    if (!file.type.startsWith('image/')) { setError('Solo se aceptan imágenes'); return }
    setError('')
    setPreview(URL.createObjectURL(file))
    setLoading(true)
    try {
      const { url } = await uploadFoto(file)
      onChange(url)
    } catch (e) {
      setError('Error al subir la foto. Intenta de nuevo.')
      setPreview(null)
      onChange(null)
    } finally {
      setLoading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    handleFile(file)
  }

  const clear = () => {
    setPreview(null)
    onChange(null)
    fileRef.current.value = ''
  }

  return (
    <div>
      <label className="block text-sm font-medium text-slate-300 mb-2">{label}</label>

      {preview ? (
        <div className="relative rounded-xl overflow-hidden border border-surface-600 group">
          <img src={preview} alt="Preview" className="w-full h-48 object-cover" />
          {loading && (
            <div className="absolute inset-0 bg-surface-900/70 flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-brand-400 animate-spin" />
            </div>
          )}
          <button
            type="button"
            onClick={clear}
            className="absolute top-2 right-2 bg-red-600 hover:bg-red-500 text-white rounded-full p-1 transition-all"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => fileRef.current.click()}
          className="border-2 border-dashed border-surface-600 hover:border-brand-600
                     rounded-xl p-8 flex flex-col items-center justify-center gap-3
                     cursor-pointer transition-all hover:bg-brand-900/10 group"
        >
          <div className="w-12 h-12 bg-surface-700 group-hover:bg-brand-700/30 rounded-xl
                          flex items-center justify-center transition-all">
            <Camera className="w-6 h-6 text-slate-500 group-hover:text-brand-400 transition-colors" />
          </div>
          <div className="text-center">
            <p className="text-slate-400 text-sm font-medium">Arrastra o haz clic para subir</p>
            <p className="text-slate-600 text-xs mt-0.5">JPG, PNG, WebP</p>
          </div>
          <div className="flex items-center gap-2 text-brand-400 text-xs border border-brand-700/50 rounded-full px-3 py-1">
            <Upload className="w-3 h-3" /> Seleccionar foto
          </div>
        </div>
      )}

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />
      {error && <p className="text-red-400 text-xs mt-1.5">{error}</p>}
    </div>
  )
}
