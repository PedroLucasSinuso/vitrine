import { AlertCircle, X } from 'lucide-react'

interface Props {
  message: string
  onDismiss?: () => void
  className?: string
}

export default function ErrorBanner({ message, onDismiss, className = '' }: Props) {
  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-xl bg-danger-light border border-danger/20 ${className}`}
      role="alert"
    >
      <AlertCircle size={16} className="text-danger shrink-0 mt-0.5" />
      <p className="text-sm text-danger flex-1">{message}</p>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-danger/60 hover:text-danger transition shrink-0"
          aria-label="Descartar"
        >
          <X size={14} />
        </button>
      )}
    </div>
  )
}
