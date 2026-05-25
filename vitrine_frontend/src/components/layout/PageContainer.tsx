import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  className?: string
}

const maxWidths: Record<string, string> = {
  sm:   'max-w-lg',
  md:   'max-w-3xl',
  lg:   'max-w-5xl',
  xl:   'max-w-6xl',
  full: 'max-w-full',
}

/**
 * PageContainer — wrapper consistente de página
 * 
 * Uso:
 * ```tsx
 * <PageContainer maxWidth="xl">
 *   <PageSection>...</PageSection>
 * </PageContainer>
 * ```
 */
export default function PageContainer({ children, maxWidth = 'xl', className = '' }: Props) {
  return (
    <div className={`flex flex-col items-center px-4 sm:px-6 py-4 sm:py-6 ${className}`}>
      <div className={`w-full ${maxWidths[maxWidth]} flex flex-col gap-6`}>
        {children}
      </div>
    </div>
  )
}
