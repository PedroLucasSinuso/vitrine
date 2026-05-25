import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  variant?: 'default' | 'bordered' | 'interactive' | 'elevated' | 'danger' | 'compact'
  className?: string
  onClick?: () => void
  padding?: 'sm' | 'md' | 'lg' | 'none'
}

const variants: Record<string, string> = {
  default:     'card-base',
  bordered:    'card-bordered',
  interactive: 'card-interactive',
  elevated:    'card-elevated',
  danger:      'bg-danger-light border border-danger/20 rounded-xl',
  compact:     'card-base p-3',
}

const paddings: Record<string, string> = {
  sm:   'p-4',
  md:   'p-5',
  lg:   'p-6',
  none: '',
}

export default function Card({
  children, variant = 'default', className = '', onClick,
  padding = variant === 'compact' ? 'none' : 'md',
}: Props) {
  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag
      onClick={onClick}
      className={`${variants[variant]} ${paddings[padding]} ${onClick ? 'text-left w-full' : ''} ${className}`}
    >
      {children}
    </Tag>
  )
}
