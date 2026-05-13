interface Props {
  className?: string
  variant?: 'text' | 'card' | 'circle' | 'table-row'
}

const variants: Record<string, string> = {
  text: 'h-4 w-full rounded',
  card: 'h-32 w-full rounded-2xl',
  circle: 'h-10 w-10 rounded-full',
  'table-row': 'h-12 w-full rounded-lg',
}

export default function Skeleton({ className = '', variant = 'text' }: Props) {
  return (
    <div
      className={`animate-pulse bg-gray-200 dark:bg-gray-700 ${variants[variant]} ${className}`}
    />
  )
}
