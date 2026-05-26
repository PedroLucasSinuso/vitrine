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
        <label className="text-xs font-medium text-text-muted">{label}</label>
        <div className="flex items-center gap-2">
          <div className="flex-1 flex items-center gap-2 form-input-base cursor-default">
            <span className="text-sm text-text-muted font-mono flex-1 truncate">
              {isConfigured ? MASKED_DISPLAY : (value || '—')}
            </span>
            {isConfigured && (
              <button
                type="button"
                onClick={() => { originalValue.current = value; setEditing(true); onChange(SENTINEL) }}
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
      <label className="text-xs font-medium text-text-muted">{label}</label>
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <input
            type={showValue ? 'text' : 'password'}
            className="form-input-base pr-8"
            value={value === SENTINEL ? '' : value}
            onChange={(e) => {
              const v = e.target.value
              if (v !== '') onChange(v)
            }}
            placeholder={placeholder ?? 'Digite o novo valor'}
            autoFocus
          />
          <button
            onClick={() => setShowValue((prev) => !prev)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition"
            title={showValue ? 'Ocultar' : 'Mostrar'}
            type="button"
          >
            {showValue ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>
        <button
          onClick={() => { setEditing(false); onChange(originalValue.current) }}
          className="text-text-muted hover:text-danger transition p-1.5 rounded-lg hover:bg-danger-light"
          title="Cancelar"
          type="button"
        >
          <X size={14} />
        </button>
      </div>
      <p className="text-[10px] text-text-muted">
        Deixe vazio para manter o valor atual
      </p>
    </div>
  )
}
