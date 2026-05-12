/* eslint-disable react-refresh/only-export-components -- Hook + Context + Provider + useToast export must coexist */
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

export type ToastType = 'success' | 'error' | 'info'

export interface ToastMessage {
  id: number
  type: ToastType
  message: string
}

interface ToastContextType {
  toasts: ToastMessage[]
  toast: (msg: { type: ToastType; message: string }) => void
  remove: (id: number) => void
}

const ToastContext = createContext<ToastContextType | null>(null)

let nextId = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = useCallback((msg: { type: ToastType; message: string }) => {
    const id = nextId++
    setToasts((prev) => [...prev, { id, type: msg.type, message: msg.message }])
    setTimeout(() => remove(id), 4000)
  }, [remove])

  return (
    <ToastContext.Provider value={{ toasts, toast, remove }}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast(): { toast: (msg: { type: ToastType; message: string }) => void } {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return { toast: ctx.toast }
}

export function useToasts(): ToastContextType {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToasts must be used within ToastProvider')
  return ctx
}
