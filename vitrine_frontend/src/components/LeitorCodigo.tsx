import { useEffect, useRef, useState, useCallback } from 'react'
import { BrowserMultiFormatReader } from '@zxing/browser'
import { X, ScanLine, CameraOff, Sun } from 'lucide-react'
import Button from './ui/Button'

interface Props {
  onLeitura: (codigo: string) => void
  onFechar: () => void
  continuo?: boolean
}

export default function LeitorCodigo({ onLeitura, onFechar, continuo = false }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [erro, setErro] = useState('')
  const [flash, setFlash] = useState(false)
  const readerRef = useRef<BrowserMultiFormatReader | null>(null)
  const controlsRef = useRef<{ stop: () => void } | null>(null)
  const hasReadRef = useRef(false)
  const stoppedRef = useRef(false)

  const onLeituraRef = useRef(onLeitura)
  useEffect(() => { onLeituraRef.current = onLeitura }, [onLeitura])

  const cleanup = useCallback(() => {
    stoppedRef.current = true
    try { controlsRef.current?.stop() } catch { /* already stopped */ }
    controlsRef.current = null
    readerRef.current = null
    BrowserMultiFormatReader.releaseAllStreams()
  }, [])

  function toggleFlash() {
    const video = videoRef.current
    if (!video) return
    const stream = video.srcObject as MediaStream | null
    const track = stream?.getVideoTracks()[0]
    if (!track) return
    const nova = !flash
    setFlash(nova)
    track.applyConstraints({ advanced: [{ torch: nova }] as Record<string, unknown>[] }).catch(() => {
      setFlash(false) // torch não suportado nesse dispositivo
    })
  }

  useEffect(() => {
    hasReadRef.current = false
    stoppedRef.current = false  // limpa trava do Strict Mode (desmonta + remonta)
    const reader = new BrowserMultiFormatReader()
    readerRef.current = reader

    reader.decodeFromVideoDevice(undefined, videoRef.current!, (result) => {
      if (stoppedRef.current) return
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

        {/* Flash toggle */}
        <button
          onClick={toggleFlash}
          className={`absolute top-3 right-3 z-10 p-2.5 rounded-xl transition ${
            flash
              ? 'bg-yellow-400 text-yellow-900 shadow-lg shadow-yellow-400/40'
              : 'bg-white/20 text-white/70 hover:bg-white/30'
          }`}
          aria-label={flash ? 'Desligar flash' : 'Ligar flash'}
          title={flash ? 'Desligar flash' : 'Ligar flash'}
        >
          <Sun size={18} />
        </button>

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
