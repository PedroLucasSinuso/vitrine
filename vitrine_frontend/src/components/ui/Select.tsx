import { forwardRef, type SelectHTMLAttributes } from 'react'
import { ChevronDown } from 'lucide-react'

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  helper?: string
  error?: string
  /** Placeholder option (desabilitado) */
  placeholder?: string
}

const Select = forwardRef<HTMLSelectElement, Props>(
  ({ label, helper, error, placeholder, children, className = '', ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label className="form-label" htmlFor={props.id}>
            {label}
          </label>
        )}

        <div className="relative">
          <select
            ref={ref}
            className={`form-input-base pr-8 ${error ? '!border-danger !ring-danger/30' : ''} ${className}`}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>{placeholder}</option>
            )}
            {children}
          </select>
          <ChevronDown
            size={14}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-text-muted"
          />
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

Select.displayName = 'Select'

export default Select
