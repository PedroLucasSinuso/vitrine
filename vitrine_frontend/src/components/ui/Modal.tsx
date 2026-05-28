import { useEffect, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

interface Props {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  variant?: 'default' | 'danger'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  actions?: ReactNode
  className?: string
}

const sizeClasses: Record<string, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-3xl',
}

export default function Modal({
  open, onClose, title, children, variant = 'default', size = 'md', actions, className = '',
}: Props) {
  const previousActiveElement = useRef<HTMLElement | null>(null)
  const scrollY = useRef(0)

  // Body scroll lock — preserva posição do scroll
  useEffect(() => {
    if (!open) return
    previousActiveElement.current = document.activeElement as HTMLElement
    scrollY.current = window.scrollY
    const prevOverflow = document.body.style.overflow
    const prevPosition = document.body.style.position
    const prevTop = document.body.style.top
    const prevWidth = document.body.style.width

    document.body.style.overflow = 'hidden'
    document.body.style.position = 'fixed'
    document.body.style.top = `-${scrollY.current}px`
    document.body.style.width = '100%'

    return () => {
      document.body.style.overflow = prevOverflow
      document.body.style.position = prevPosition
      document.body.style.top = prevTop
      document.body.style.width = prevWidth
      window.scrollTo(0, scrollY.current)
      previousActiveElement.current?.focus()
    }
  }, [open])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-[100] overflow-y-auto">
      {/* Backdrop — cobre 100vw x 100vh, desacoplado de qualquer pai */}
      <div
        className="fixed inset-0 bg-bg-modal-overlay backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog — centralizado na viewport, sem influência de containers ancestrais */}
      <div className="flex min-h-screen items-center justify-center p-4 relative pointer-events-none">
        <div
          className={`
            pointer-events-auto
            bg-surface-modal rounded-xl shadow-modal
            w-full sm:w-[90vw] ${sizeClasses[size]}
            animate-scale-in
            ${className}
          `}
          role="dialog"
          aria-modal="true"
          aria-label={title || undefined}
        >
          {/* Header */}
          {title && (
            <div className="flex items-center justify-between px-5 pt-5 pb-3">
              <h2 className={`text-lg font-bold text-text-primary font-display ${variant === 'danger' ? 'text-danger' : ''}`}>
                {title}
              </h2>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-hover transition"
                aria-label="Fechar"
              >
                <X size={16} />
              </button>
            </div>
          )}

          {/* Content */}
          <div className="px-5 pb-5">
            {children}
          </div>

          {/* Actions */}
          {actions && (
            <div className="flex items-center justify-end gap-2 px-5 pb-5 pt-0">
              {actions}
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  )
}
