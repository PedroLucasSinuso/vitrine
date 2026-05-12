import { useEffect, useRef, useState } from 'react'
import { BrowserMultiFormatReader } from '@zxing/browser'

interface Props {
  onLeitura: (codigo: string) => void
  onFechar: () => void
}

export default function LeitorCodigo({ onLeitura, onFechar }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [erro, setErro] = useState('')
  const leuRef = useRef(false)
  const readerRef = useRef<BrowserMultiFormatReader | null>(null)
  const controlsRef = useRef<{ stop: () => void } | null>(null)

  const onLeituraRef = useRef(onLeitura)
  const onFecharRef = useRef(onFechar)
  useEffect(() => { onLeituraRef.current = onLeitura }, [onLeitura])
  useEffect(() => { onFecharRef.current = onFechar }, [onFechar])

  function cleanup() {
    try {
      controlsRef.current?.stop()
    } catch {
      // ignora se já parado
    }
    controlsRef.current = null
    readerRef.current = null
    BrowserMultiFormatReader.releaseAllStreams()
  }

  useEffect(() => {
    const reader = new BrowserMultiFormatReader()
    readerRef.current = reader
    leuRef.current = false

    reader.decodeFromVideoDevice(undefined, videoRef.current!, (result) => {
      if (result && !leuRef.current) {
        leuRef.current = true
        cleanup()
        onLeituraRef.current(result.getText())
      }
    })
      .then(controls => {
        controlsRef.current = controls
      })
      .catch(() => {
        setErro('Não foi possível acessar a câmera. Verifique as permissões.')
      })

    return cleanup
  }, [])

  function handleCancelar() {
    cleanup()
    onFecharRef.current()
  }

  return (
    <div className="fixed inset-0 bg-black/80 dark:bg-black/90 flex flex-col items-center justify-center z-50 px-4">
      <div className="w-full max-w-sm bg-black dark:bg-gray-900 rounded-2xl overflow-hidden">
        <div className="relative">
          <video ref={videoRef} className="w-full" autoPlay muted playsInline />
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-48 h-24 border-2 border-white rounded-lg opacity-60" />
          </div>
        </div>

        {erro && (
          <p className="text-red-400 text-sm text-center px-4 py-3">{erro}</p>
        )}

        <div className="p-4">
          <p className="text-gray-400 text-xs text-center mb-3">
            Aponte para o código de barras
          </p>
          <button
            onClick={handleCancelar}
            className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 rounded-lg transition"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}