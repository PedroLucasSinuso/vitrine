import { useRef, useState } from 'react'
import { Eye, EyeOff, Pencil, X } from 'lucide-react'

const SENTINEL = '***configurado***'
const MASKED_DISPLAY = '••••••••'

interface Props {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export default function PasswordConfigInput({ label, value, onChange, placeholder }: Props) {
  const isConfigured = value === SENTINEL
  const [editing, setEditing] = useState(false)
  const [showValue, setShowValue] = useState(false)
  const originalValue = useRef(value)

  // When not editing, show masked dots if configured
  if (!editing) {
    return (
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</label>
        <div className="flex items-center gap-2">
          <div className="flex-1 flex items-center gap-2 border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 rounded-lg px-3 py-2">
            <span className="text-sm text-slate-400 dark:text-slate-500 font-mono flex-1 truncate">
              {isConfigured ? MASKED_DISPLAY : (value || '—')}
            </span>
            {isConfigured && (
              <button
                type="button"
                onClick={() => { originalValue.current = value; setEditing(true); onChange('') }}
                className="text-xs text-primary hover:text-primary-hover font-medium transition shrink-0"
                title="Editar"
              >
                <Pencil size={13} />
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Editing mode — field is empty, user types new value
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</label>
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <input
            type={showValue ? 'text' : 'password'}
            className="w-full border border-primary/50 dark:border-primary/30 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 pr-8 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder ?? 'Digite o novo valor'}
            autoFocus
          />
          <button
            onClick={() => setShowValue((prev) => !prev)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition"
            title={showValue ? 'Ocultar' : 'Mostrar'}
            type="button"
          >
            {showValue ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>
        <button
          onClick={() => { setEditing(false); onChange(originalValue.current) }}
          className="text-slate-400 hover:text-red-500 transition p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
          title="Cancelar"
          type="button"
        >
          <X size={14} />
        </button>
      </div>
      <p className="text-[10px] text-slate-400 dark:text-slate-500">
        Deixe vazio para manter o valor atual
      </p>
    </div>
  )
}
