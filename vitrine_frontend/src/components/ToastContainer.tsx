import { useToasts } from '../hooks/useToast'
import { CheckCircle, XCircle, Info, X } from 'lucide-react'

const icons: Record<string, React.ReactNode> = {
  success: <CheckCircle size={16} className="text-green-600 dark:text-green-400" />,
  error: <XCircle size={16} className="text-red-600 dark:text-red-400" />,
  info: <Info size={16} className="text-blue-600 dark:text-blue-400" />,
}

const bgColors: Record<string, string> = {
  success: 'bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-900',
  error: 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-900',
  info: 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-900',
}

export default function ToastContainer() {
  const { toasts, remove } = useToasts()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 w-[90vw] max-w-sm">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg border ${bgColors[toast.type]} animate-fade-in-up`}
        >
          {icons[toast.type]}
          <p className="text-sm font-medium text-slate-800 dark:text-slate-100 flex-1">{toast.message}</p>
          <button onClick={() => remove(toast.id)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  )
}
