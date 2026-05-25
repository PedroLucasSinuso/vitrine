import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'default'
  dot?: boolean
  pulse?: boolean
  className?: string
}

const variantClasses: Record<string, string> = {
  success: 'bg-success-light text-success border-success/20',
  warning: 'bg-warning-light text-warning border-warning/20',
  danger:  'bg-danger-light text-danger border-danger/20',
  info:    'bg-info/10 text-info border-info/20',
  default: 'bg-bg-hover text-text-secondary border-border/40',
}

export default function Badge({
  children, variant = 'default', dot = false, pulse = false, className = '',
}: Props) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${variantClasses[variant]} ${className}`}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${pulse ? 'animate-pulse' : ''} ${
            variant === 'success' ? 'bg-success'
            : variant === 'warning' ? 'bg-warning'
            : variant === 'danger' ? 'bg-danger'
            : variant === 'info' ? 'bg-info'
            : 'bg-text-muted'
          }`}
        />
      )}
      {children}
    </span>
  )
}
