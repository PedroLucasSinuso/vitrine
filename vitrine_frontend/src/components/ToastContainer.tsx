import { useToasts } from '../hooks/useToast'

const STYLES = {
  success: 'bg-green-600 text-white',
  error: 'bg-red-600 text-white',
  info: 'bg-primary text-white',
}

export default function ToastContainer() {
  const { toasts, remove } = useToasts()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 w-full max-w-sm px-4">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="alert"
          className={`${STYLES[t.type]} px-4 py-3 rounded-xl shadow-lg text-sm font-semibold flex items-center justify-between gap-3 animate-[slideUp_0.3s_ease-out]`}
        >
          <span>{t.message}</span>
          <button
            onClick={() => remove(t.id)}
            className="text-white/70 hover:text-white transition text-lg leading-none"
            aria-label="Fechar"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
