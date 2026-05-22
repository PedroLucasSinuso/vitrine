import { forwardRef } from 'react'
import type { ReactNode, InputHTMLAttributes } from 'react'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  helperText?: string
  error?: string
  icon?: ReactNode
  loading?: boolean
  fullWidth?: boolean
}

const Input = forwardRef<HTMLInputElement, Props>(
  ({ label, helperText, error, icon, loading, fullWidth, className = '', ...props }, ref) => {
    return (
      <div className={`${fullWidth ? 'w-full' : ''}`}>
        {label && (
          <label className="block text-xs font-semibold text-text-secondary mb-1">{label}</label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-text-muted">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            {...props}
            className={`w-full border rounded-lg px-4 py-2 text-sm bg-bg-input text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-border-focus focus:border-border-focus transition ${
              error
                ? 'border-danger'
                : 'border-border-input'
            } ${icon ? 'pl-10' : ''} ${loading ? 'opacity-60' : ''} ${className}`}
          />
          {loading && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
        {error && <p className="text-xs text-danger mt-1">{error}</p>}
        {helperText && !error && <p className="text-xs text-text-muted mt-1">{helperText}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'
export default Input
