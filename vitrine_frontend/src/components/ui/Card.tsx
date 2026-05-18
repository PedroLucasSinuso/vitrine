import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  variant?: 'default' | 'bordered' | 'interactive' | 'elevated' | 'danger' | 'compact'
  className?: string
  onClick?: () => void
}

const variants: Record<string, string> = {
  default: 'bg-white dark:bg-slate-800 shadow-sm',
  bordered: 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/50 shadow-sm',
  interactive: 'bg-white dark:bg-slate-800 shadow-sm hover:shadow-md hover:ring-1 hover:ring-primary-lighter dark:hover:ring-primary cursor-pointer card-hover',
  elevated: 'bg-white dark:bg-slate-800 shadow-lg',
  danger: 'bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900',
  compact: 'bg-white dark:bg-slate-800 shadow-sm p-3',
}

const rounded: Record<string, string> = {
  default: 'rounded-2xl',
  bordered: 'rounded-xl',
  interactive: 'rounded-2xl',
  elevated: 'rounded-2xl',
  danger: 'rounded-xl',
  compact: 'rounded-2xl',
}

const paddings: Record<string, string> = {
  default: 'p-5',
  bordered: 'p-5',
  interactive: 'p-5',
  elevated: 'p-5',
  danger: 'p-5',
  compact: '',
}

export default function Card({ children, variant = 'default', className = '', onClick }: Props) {
  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag
      onClick={onClick}
      className={`${rounded[variant]} ${variants[variant]} ${paddings[variant]} ${onClick ? 'text-left w-full' : ''} ${className}`}
    >
      {children}
    </Tag>
  )
}
