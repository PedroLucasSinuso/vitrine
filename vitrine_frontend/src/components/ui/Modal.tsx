import { useEffect, useRef, type ReactNode } from 'react'
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

  useEffect(() => {
    if (!open) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 animate-fade-in-up"
      onClick={(e) => { if (e.target === overlayRef.current) onClose() }}
    >
      <div
        className={`w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl shadow-xl animate-fade-in-up ${
          variant === 'danger'
            ? 'bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900'
            : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700'
        }`}
      >
        <div className="flex items-center justify-between px-5 pt-5 pb-3">
          <h2 className={`text-base font-bold ${variant === 'danger' ? 'text-red-700 dark:text-red-300' : 'text-gray-800 dark:text-gray-100'}`}>
            {title}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition p-1">
            <X size={18} />
          </button>
        </div>
        <div className="px-5 pb-4 text-sm text-gray-600 dark:text-gray-300">
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
