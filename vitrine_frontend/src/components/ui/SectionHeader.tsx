import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { ArrowRight } from 'lucide-react'

interface Props {
  icon?: LucideIcon
  children: ReactNode
  action?: { label: string; onClick: () => void }
}

export default function SectionHeader({ icon: Icon, children, action }: Props) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2">
        {Icon && <Icon size={16} className="text-primary" aria-hidden="true" />}
        <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200">{children}</h2>
      </div>
      {action && (
        <button
          onClick={action.onClick}
          className="text-xs text-primary hover:text-primary-hover font-medium flex items-center gap-1 transition"
        >
          {action.label} <ArrowRight size={12} />
        </button>
      )}
    </div>
  )
}
