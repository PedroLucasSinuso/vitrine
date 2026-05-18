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
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">{label}</label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-slate-400">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            {...props}
            className={`w-full border rounded-lg px-4 py-2 text-sm bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary transition ${
              error
                ? 'border-red-400 dark:border-red-500'
                : 'border-slate-300 dark:border-slate-600'
            } ${icon ? 'pl-10' : ''} ${loading ? 'opacity-60' : ''} ${className}`}
          />
          {loading && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
        {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
        {helperText && !error && <p className="text-xs text-slate-400 mt-1">{helperText}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'
export default Input
