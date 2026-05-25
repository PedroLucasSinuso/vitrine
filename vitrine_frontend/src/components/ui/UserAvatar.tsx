interface Props {
  name: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const AVATAR_COLORS = [
  { bg: 'bg-primary/10', text: 'text-primary', darkBg: 'dark:bg-primary/20' },
  { bg: 'bg-info/10', text: 'text-info', darkBg: '' },
  { bg: 'bg-amber-100', text: 'text-amber-700', darkBg: 'dark:bg-amber-900/30 dark:text-amber-400' },
  { bg: 'bg-purple-100', text: 'text-purple-700', darkBg: 'dark:bg-purple-900/30 dark:text-purple-400' },
  { bg: 'bg-emerald-100', text: 'text-emerald-700', darkBg: 'dark:bg-emerald-900/30 dark:text-emerald-400' },
  { bg: 'bg-rose-100', text: 'text-rose-700', darkBg: 'dark:bg-rose-900/30 dark:text-rose-400' },
  { bg: 'bg-cyan-100', text: 'text-cyan-700', darkBg: 'dark:bg-cyan-900/30 dark:text-cyan-400' },
  { bg: 'bg-orange-100', text: 'text-orange-700', darkBg: 'dark:bg-orange-900/30 dark:text-orange-400' },
]

const SIZE_MAP = {
  sm: 'w-8 h-8 text-xs rounded-lg',
  md: 'w-10 h-10 text-sm rounded-xl',
  lg: 'w-12 h-12 text-base rounded-xl',
}

/**
 * UserAvatar — avatar genérico com iniciais e cor derivada do nome.
 * Usado na Sidebar, listas de usuários, etc.
 * Nunca exibe foto real — apenas ilustrações abstratas com iniciais.
 */
export default function UserAvatar({ name, size = 'md', className = '' }: Props) {
  const initials = name
    .split(' ')
    .map(n => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase()

  const colorIdx = name.charCodeAt(0) % AVATAR_COLORS.length
  const color = AVATAR_COLORS[colorIdx]

  return (
    <div
      className={`${SIZE_MAP[size]} ${color.bg} ${color.text} ${color.darkBg} flex items-center justify-center font-bold shrink-0 ${className}`}
      aria-hidden="true"
    >
      {initials}
    </div>
  )
}
