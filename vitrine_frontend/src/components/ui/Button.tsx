import { Loader2 } from 'lucide-react'

interface Props {
  children: React.ReactNode
  onClick?: () => void
  type?: 'button' | 'submit'
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  className?: string
  fullWidth?: boolean
}

const variants: Record<string, string> = {
  primary:   'bg-primary text-white hover:bg-primary-hover shadow-sm',
  secondary: 'bg-bg-card border border-border text-text-secondary hover:bg-bg-hover hover:text-text-primary',
  ghost:     'text-text-secondary hover:bg-bg-hover hover:text-text-primary',
  danger:    'bg-danger text-white hover:bg-red-600',
  outline:   'border border-primary text-primary hover:bg-primary hover:text-white',
}

const sizes: Record<string, string> = {
  sm: 'text-xs px-3 py-1.5 rounded-lg',
  md: 'text-sm px-4 py-2.5 rounded-xl',
  lg: 'text-base px-6 py-3 rounded-xl',
}

export default function Button({
  children, onClick, type = 'button', variant = 'primary',
  size = 'md', loading = false, disabled = false, className = '', fullWidth,
}: Props) {
  const isDisabled = disabled || loading
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      className={`font-semibold transition-all duration-fast flex items-center justify-center gap-2 active:scale-[0.97] ${
        variants[variant]} ${sizes[size]} ${fullWidth ? 'w-full' : ''} ${
        isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
      } ${className}`}
    >
      {loading && <Loader2 size={size === 'sm' ? 14 : 16} className="animate-spin" />}
      {children}
    </button>
  )
}
