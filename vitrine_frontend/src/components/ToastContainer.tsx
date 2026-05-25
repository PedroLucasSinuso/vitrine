import { useToasts } from '../hooks/useToast'
import { CheckCircle, XCircle, Info, X } from 'lucide-react'

const icons: Record<string, React.ReactNode> = {
  success: <CheckCircle size={16} className="text-success" />,
  error: <XCircle size={16} className="text-danger" />,
  info: <Info size={16} className="text-info" />,
}

const bgColors: Record<string, string> = {
  success: 'bg-success-light border-success/20',
  error: 'bg-danger-light border-danger/20',
  info: 'bg-info/10 border-info/20',
}

export default function ToastContainer() {
  const { toasts, remove } = useToasts()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 lg:bottom-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 w-[90vw] max-w-sm">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg border ${bgColors[toast.type]} animate-fade-in-up`}
        >
          {icons[toast.type]}
          <p className="text-sm font-medium text-text-primary flex-1">{toast.message}</p>
          <button onClick={() => remove(toast.id)} className="text-text-muted hover:text-text-secondary transition">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
