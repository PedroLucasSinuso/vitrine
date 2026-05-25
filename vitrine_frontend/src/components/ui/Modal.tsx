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
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(false)

  // Track mount status to prevent setState on unmounted component
  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  // Handle mount/unmount + animation based on open prop
  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMounted(true)
      const t = requestAnimationFrame(() => setShow(true))
      return () => cancelAnimationFrame(t)
    } else {
      setShow(false)
      closeTimer.current = setTimeout(() => {
        if (mountedRef.current) setMounted(false)
      }, 200)
      return () => {
        if (closeTimer.current) clearTimeout(closeTimer.current)
      }
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
      className={`fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-bg-modal-overlay backdrop-blur-sm ${
        isExiting ? 'animate-fade-out' : 'animate-fade-in-up'
      }`}
      onClick={handleOverlayClick}
    >
      <div
        className={`w-full sm:max-w-md rounded-t-2xl sm:rounded-xl shadow-modal ${
          isExiting ? 'animate-slide-down' : 'animate-scale-in'
        } ${
          variant === 'danger'
            ? 'bg-danger-light border border-danger/20'
            : 'bg-surface-modal border border-border'
        }`}
      >
        <div className="flex items-center justify-between px-5 pt-5 pb-3">
          <h2 id="modal-title" className={`text-base font-bold ${
            variant === 'danger' ? 'text-danger' : 'text-text-primary'
          }`}>
            {title}
          </h2>
          <button
            onClick={handleClose}
            aria-label="Fechar"
            className="text-text-muted hover:text-text-secondary transition p-1"
          >
            <X size={18} />
          </button>
        </div>
        <div className="px-5 pb-4 text-sm text-text-secondary">
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
