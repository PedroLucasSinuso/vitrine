import type { ReactNode } from 'react'

interface Props {
  label: string
  htmlFor?: string
  error?: string
  helper?: string
  children: ReactNode
  className?: string
  required?: boolean
}

/**
 * FormField — wrapper consistente para campos de formulário
 * 
 * Uso:
 * ```tsx
 * <FormField label="E-mail" error={errors.email}>
 *   <Input {...register('email')} />
 * </FormField>
 * ```
 */
export default function FormField({
  label, htmlFor, error, helper, children, className = '', required,
}: Props) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label
        htmlFor={htmlFor}
        className="form-label"
      >
        {label}
        {required && <span className="text-danger ml-0.5">*</span>}
      </label>

      {children}

      {helper && !error && (
        <p className="text-xs text-text-muted">{helper}</p>
      )}

      {error && (
        <p className="form-error">{error}</p>
      )}
    </div>
  )
}
