import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  variant?: 'default' | 'bordered' | 'interactive' | 'elevated' | 'danger' | 'compact'
  className?: string
  onClick?: () => void
}

const variants: Record<string, string> = {
  default:     'bg-bg-card shadow-card',
  bordered:    'bg-bg-card border border-border shadow-card',
  interactive: 'bg-bg-card shadow-card hover:shadow-card-hover hover:border-border-light hover:ring-1 hover:ring-primary/20 cursor-pointer',
  elevated:    'bg-bg-card shadow-card-hover',
  danger:      'bg-danger-light border border-danger/20',
  compact:     'bg-bg-card shadow-card p-3',
}

const rounded: Record<string, string> = {
  default:     'rounded-xl',
  bordered:    'rounded-xl',
  interactive: 'rounded-xl',
  elevated:    'rounded-xl',
  danger:      'rounded-xl',
  compact:     'rounded-xl',
}

const paddings: Record<string, string> = {
  default:     'p-5',
  bordered:    'p-5',
  interactive: 'p-5',
  elevated:    'p-5',
  danger:      'p-5',
  compact:     '',
}

export default function Card({ children, variant = 'default', className = '', onClick }: Props) {
  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag
      onClick={onClick}
      className={`${rounded[variant]} ${variants[variant]} ${paddings[variant]} ${onClick ? 'text-left w-full' : ''} transition-all duration-fast ${className}`}
    >
      {children}
    </Tag>
  )
}
