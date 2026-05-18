import { AlertCircle, X } from 'lucide-react'

interface Props {
  message: string
  onDismiss?: () => void
}

export default function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 rounded-xl p-4 flex items-start gap-3">
      <AlertCircle size={16} className="text-red-500 shrink-0 mt-0.5" />
      <p className="text-sm text-red-600 dark:text-red-400 flex-1">{message}</p>
      {onDismiss && (
        <button onClick={onDismiss} className="text-red-400 hover:text-red-600 transition shrink-0">
          <X size={14} />
        </button>
      )}
    </div>
  )
}
