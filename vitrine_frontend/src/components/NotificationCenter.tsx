import { useState, useRef, useEffect } from 'react'
import { Bell, BellOff } from 'lucide-react'

interface Notificacao {
  id: string
  tipo: 'info' | 'warning' | 'success' | 'error'
  mensagem: string
  lida: boolean
  createdAt: string
}

// Placeholder — integrar com backend futuramente via WebSocket ou polling
const NOTIFICACOES: Notificacao[] = []

export default function NotificationCenter() {
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [open])

  const naoLidas = NOTIFICACOES.filter((n) => !n.lida).length

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="relative text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
        aria-label="Notificações"
        aria-expanded={open}
        aria-haspopup="true"
        title="Notificações"
      >
        <Bell size={15} aria-hidden="true" />
        {naoLidas > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-red-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center">
            {naoLidas > 9 ? '9+' : naoLidas}
          </span>
        )}
      </button>

      {open && (
        <div
          role="menu"
          aria-label="Notificações"
          className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 animate-fade-in-up z-[60]"
        >
          <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Notificações</h3>
          </div>

          {NOTIFICACOES.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-slate-400 dark:text-slate-500">
              <BellOff size={24} className="mx-auto mb-2 opacity-40" aria-hidden="true" />
              Nenhuma notificação
            </div>
          ) : (
            <div className="max-h-72 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700">
              {NOTIFICACOES.map((n) => (
                <div key={n.id} className={`px-4 py-3 text-sm ${n.lida ? 'opacity-60' : ''}`}>
                  <p className="text-slate-700 dark:text-slate-300">{n.mensagem}</p>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-1">{n.createdAt}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
