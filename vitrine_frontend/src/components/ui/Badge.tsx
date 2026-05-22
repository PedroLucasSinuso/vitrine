import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'default'
  dot?: boolean
  dotPulse?: boolean
  className?: string
}

const variantStyles: Record<string, string> = {
  success: 'bg-success-light text-success border border-success/20',
  warning: 'bg-warning-light text-warning border border-warning/20',
  danger:  'bg-danger-light text-danger border border-danger/20',
  info:    'bg-primary-light text-primary border border-primary/20',
  default: 'bg-bg-card text-text-secondary border border-border',
}

const dotColors: Record<string, string> = {
  success: 'bg-success',
  warning: 'bg-warning',
  danger:  'bg-danger',
  info:    'bg-primary',
  default: 'bg-text-muted',
}

export default function Badge({
  children, variant = 'default', dot = false, dotPulse = false, className = '',
}: Props) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
        variantStyles[variant]
      } ${className}`}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]} ${
            dotPulse ? 'animate-pulse' : ''
          }`}
        />
      )}
      {children}
    </span>
  )
}
