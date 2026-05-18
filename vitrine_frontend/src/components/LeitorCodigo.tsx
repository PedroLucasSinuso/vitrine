import { useEffect, useRef, useState, useCallback } from 'react'
import { BrowserMultiFormatReader } from '@zxing/browser'
import { X, ScanLine, CameraOff } from 'lucide-react'
import Button from './ui/Button'

interface Props {
  onLeitura: (codigo: string) => void
  onFechar: () => void
  continuo?: boolean
}

export default function LeitorCodigo({ onLeitura, onFechar, continuo = false }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [erro, setErro] = useState('')
  const readerRef = useRef<BrowserMultiFormatReader | null>(null)
  const controlsRef = useRef<{ stop: () => void } | null>(null)
  const hasReadRef = useRef(false)

  const onLeituraRef = useRef(onLeitura)
  useEffect(() => { onLeituraRef.current = onLeitura }, [onLeitura])

  const cleanup = useCallback(() => {
    try { controlsRef.current?.stop() } catch { /* already stopped */ }
    controlsRef.current = null
    readerRef.current = null
    BrowserMultiFormatReader.releaseAllStreams()
  }, [])

  useEffect(() => {
    hasReadRef.current = false
    const reader = new BrowserMultiFormatReader()
    readerRef.current = reader

    reader.decodeFromVideoDevice(undefined, videoRef.current!, (result) => {
      if (result && (continuo || !hasReadRef.current)) {
        if (!continuo) hasReadRef.current = true
        navigator.vibrate?.(20)
        onLeituraRef.current(result.getText())
        if (!continuo) {
          cleanup()
          // Defer close to next tick so state updates propagate first
          setTimeout(() => onFechar(), 50)
        }
      }
    })
      .then(controls => { controlsRef.current = controls })
      .catch(() => setErro('Não foi possível acessar a câmera. Verifique as permissões.'))

    return cleanup
  }, [continuo, cleanup, onFechar])

  return (
    <div className="fixed inset-0 bg-black/90 z-50 flex flex-col items-center justify-center px-4">
      <div className="relative w-full max-w-sm bg-slate-950 rounded-2xl overflow-hidden">
        <video ref={videoRef} className="w-full aspect-[4/3] object-cover" autoPlay muted playsInline />

        {/* Scan frame overlay */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="relative">
            <ScanLine size={40} className="text-white/30" />
          </div>
        </div>

        {erro && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 gap-3">
            <CameraOff size={32} className="text-red-400" />
            <p className="text-red-400 text-sm text-center px-6">{erro}</p>
            <Button variant="secondary" size="sm" onClick={() => onFechar()}>Fechar</Button>
          </div>
        )}
      </div>

      <div className="w-full max-w-sm mt-4 flex items-center justify-between">
        <p className="text-slate-500 text-xs">
          {continuo ? 'Escaneio contínuo — aponte para o código' : 'Aponte para o código de barras'}
        </p>
        <button
          onClick={() => { cleanup(); onFechar() }}
          className="text-slate-400 hover:text-white transition flex items-center gap-1 text-sm"
        >
          <X size={16} /> Fechar
        </button>
      </div>
    </div>
  )
}
