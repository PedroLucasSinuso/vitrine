import { useState, useEffect, useRef } from 'react'

export function useCountUp(target: number, duration = 600, enabled = true): number {
  const [value, setValue] = useState(enabled ? 0 : target)
  const rafRef = useRef<number>(0)
  const prevTargetRef = useRef<number | null>(null)
  const lastValueRef = useRef<number>(0)

  useEffect(() => {
    if (!enabled || target === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Intentional: skip animation for disabled/zero targets
      setValue(target)
      lastValueRef.current = target
      prevTargetRef.current = null
      return
    }

    const start = performance.now()
    // If target changed mid-animation, start from last displayed value instead of 0
    const targetChanged = prevTargetRef.current !== null && prevTargetRef.current !== target
    const from = targetChanged ? lastValueRef.current : 0
    prevTargetRef.current = target

    function tick(now: number) {
      const elapsed = now - start
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = from + (target - from) * eased
      setValue(current)
      lastValueRef.current = current
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick)
      } else {
        setValue(target)
        lastValueRef.current = target
      }
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [target, duration, enabled])

  return value
}
