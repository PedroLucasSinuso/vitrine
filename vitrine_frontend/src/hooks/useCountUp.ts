import { useState, useEffect, useRef } from 'react'

export function useCountUp(target: number, duration = 600, enabled = true): number {
  const [value, setValue] = useState(enabled ? 0 : target)
  const rafRef = useRef<number>(0)

  useEffect(() => {
    if (!enabled || target === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Intentional: skip animation for disabled/zero targets
      setValue(target)
      return
    }

    const start = performance.now()
    const from = 0

    function tick(now: number) {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(from + (target - from) * eased)
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick)
      } else {
        setValue(target)
      }
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [target, duration, enabled])

  return value
}
