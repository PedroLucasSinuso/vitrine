import type { ReactNode } from 'react'
import { Inbox } from 'lucide-react'

interface Props {
  title: string
  description?: string
  icon?: ReactNode
  action?: ReactNode
  className?: string
}

export default function EmptyState({
  title, description, icon, action, className = '',
}: Props) {
  return (
    <div className={`card-base p-8 sm:p-10 ${className}`}>
      <div className="flex flex-col items-center text-center gap-3">
        <div className="w-12 h-12 rounded-2xl bg-bg-hover flex items-center justify-center text-text-muted">
          {icon ?? <Inbox size={24} />}
        </div>
        <div>
          <p className="text-base font-semibold text-text-primary">{title}</p>
          {description && (
            <p className="text-sm text-text-muted mt-1 max-w-sm">{description}</p>
          )}
        </div>
        {action && <div className="mt-2">{action}</div>}
      </div>
    </div>
  )
}
