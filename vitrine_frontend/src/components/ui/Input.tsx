import { forwardRef, type InputHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  helper?: string
  error?: string
  icon?: React.ReactNode
  loading?: boolean
}

const Input = forwardRef<HTMLInputElement, Props>(
  ({ label, helper, error, icon, loading, className = '', ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label className="form-label" htmlFor={props.id}>
            {label}
          </label>
        )}

        <div className="relative">
          {icon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none">
              {icon}
            </span>
          )}

          <input
            ref={ref}
            className={`form-input-base ${icon ? 'pl-9' : ''} ${error ? '!border-danger !ring-danger/30' : ''} ${className}`}
            {...props}
          />

          {loading && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted">
              <Loader2 size={14} className="animate-spin" />
            </span>
          )}
        </div>

        {helper && !error && (
          <p className="text-xs text-text-muted">{helper}</p>
        )}

        {error && (
          <p className="form-error">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input
