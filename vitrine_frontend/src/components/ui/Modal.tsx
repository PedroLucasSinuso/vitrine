import { useEffect, useRef, useState, type ReactNode } from 'react'
import { X } from 'lucide-react'

interface Props {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  variant?: 'default' | 'danger'
  actions?: ReactNode
}

export default function Modal({ open, onClose, title, children, variant = 'default', actions }: Props) {
  const overlayRef = useRef<HTMLDivElement>(null)
  const [mounted, setMounted] = useState(false)
  const [show, setShow] = useState(false)
  const closeTimer = useRef<ReturnType<typeof setTimeout>>()
  const mountedRef = useRef(false)

  // Track mount status to prevent setState on unmounted component
  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  // Handle mount/unmount + animation based on open prop
  useEffect(() => {
    if (open) {
      // eslint-disable-next-line
      setMounted(true)
      const t = requestAnimationFrame(() => setShow(true))
      return () => cancelAnimationFrame(t)
    } else {
      setShow(false)
      closeTimer.current = setTimeout(() => {
        if (mountedRef.current) setMounted(false)
      }, 200)
      return () => clearTimeout(closeTimer.current)
    }
  }, [open])

  useEffect(() => {
    if (!mounted) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
    }
  }, [mounted, onClose])

  if (!mounted) return null

  const isExiting = !show

  function handleOverlayClick(e: React.MouseEvent) {
    if (e.target === overlayRef.current) onClose()
  }

  function handleClose() {
    setShow(false)
    onClose()
  }

  return (
    <div
      ref={overlayRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className={`fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 ${
        isExiting ? 'animate-fade-out' : 'animate-fade-in-up'
      }`}
      onClick={handleOverlayClick}
    >
      <div
        className={`w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl shadow-xl ${
          isExiting ? 'animate-slide-down' : 'animate-fade-in-up'
        } ${
          variant === 'danger'
            ? 'bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900'
            : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700'
        }`}
      >
        <div className="flex items-center justify-between px-5 pt-5 pb-3">
          <h2 id="modal-title" className={`text-base font-bold ${variant === 'danger' ? 'text-red-700 dark:text-red-300' : 'text-slate-800 dark:text-slate-100'}`}>
            {title}
          </h2>
          <button
            onClick={handleClose}
            aria-label="Fechar"
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition p-1"
          >
            <X size={18} />
          </button>
        </div>
        <div className="px-5 pb-4 text-sm text-slate-600 dark:text-slate-300">
          {children}
        </div>
        {actions && (
          <div className="flex gap-2 px-5 pb-5 justify-end">
            {actions}
          </div>
        )}
      </div>
    </div>
  )
}
