/* eslint-disable react-refresh/only-export-components -- Hook + Context + Provider must coexist in one file to avoid circular imports and breaking 10+ consumers */
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

type ToastType = 'success' | 'error' | 'info'

interface ToastMessage {
  id: number
  type: ToastType
  message: string
}

interface ToastContextType {
  toasts: ToastMessage[]
  toast: (msg: Omit<ToastMessage, 'id'>) => void
  remove: (id: number) => void
}

const ToastContext = createContext<ToastContextType | null>(null)

let nextId = 0

const durations: Record<ToastType, number> = {
  success: 3000,
  error: 6000,
  info: 4000,
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const toastFn = useCallback((msg: Omit<ToastMessage, 'id'>) => {
    const id = nextId++
    setToasts(prev => [...prev, { ...msg, id }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, durations[msg.type])
  }, [])

  const remove = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, toast: toastFn, remove }}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return { toast: ctx.toast }
}

export function useToasts() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToasts must be used within ToastProvider')
  return ctx
}
