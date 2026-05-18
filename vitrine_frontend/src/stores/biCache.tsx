/* eslint-disable react-refresh/only-export-components -- Hook + Context + Provider must coexist in one file */
import { createContext, useContext, useRef, useCallback, type ReactNode } from 'react'
import type { PeriodoBi } from '../types'

interface CacheEntry {
  data: unknown
  periodoKey: string
  timestamp: number
}

interface BiCacheContextType {
  get: <T>(key: string, periodo: PeriodoBi) => T | null
  set: (key: string, periodo: PeriodoBi, data: unknown) => void
  invalidate: (key: string) => void
  clear: () => void
  getTimestamp: (key: string, periodo: PeriodoBi) => number | null
}

function periodoKey(p: PeriodoBi): string {
  return `${p.data_inicio}_${p.data_fim}`
}

const BiCacheContext = createContext<BiCacheContextType | null>(null)

export function BiCacheProvider({ children }: { children: ReactNode }) {
  const cacheRef = useRef<Map<string, CacheEntry>>(new Map())

  const get = useCallback(<T,>(key: string, periodo: PeriodoBi): T | null => {
    const entry = cacheRef.current.get(key)
    if (!entry) return null
    if (entry.periodoKey !== periodoKey(periodo)) {
      cacheRef.current.delete(key)
      return null
    }
    return entry.data as T
  }, [])

  const set = useCallback((key: string, periodo: PeriodoBi, data: unknown) => {
    cacheRef.current.set(key, { data, periodoKey: periodoKey(periodo), timestamp: Date.now() })
  }, [])

  const invalidate = useCallback((key: string) => {
    cacheRef.current.delete(key)
  }, [])

  const clear = useCallback(() => {
    cacheRef.current.clear()
  }, [])

  const getTimestamp = useCallback((key: string, periodo: PeriodoBi): number | null => {
    const entry = cacheRef.current.get(key)
    if (!entry) return null
    if (entry.periodoKey !== periodoKey(periodo)) {
      cacheRef.current.delete(key)
      return null
    }
    return entry.timestamp
  }, [])

  return (
    <BiCacheContext.Provider value={{ get, set, invalidate, clear, getTimestamp }}>
      {children}
    </BiCacheContext.Provider>
  )
}

export function useBiCache(): BiCacheContextType {
  const ctx = useContext(BiCacheContext)
  if (!ctx) throw new Error('useBiCache must be used within BiCacheProvider')
  return ctx
}
