/* eslint-disable react-refresh/only-export-components -- Hook + Context + Provider must coexist in one file */
import { createContext, useContext, useRef, useCallback, type ReactNode } from 'react'
import type { PeriodoBi } from '../types'

const MAX_ENTRIES = 50

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
  const insertionOrderRef = useRef<string[]>([])

  // Helper: resolve entry + limpa stale (m7 — extraído para evitar duplicação)
  const _resolveEntry = useCallback((key: string, periodo: PeriodoBi): CacheEntry | undefined => {
    const entry = cacheRef.current.get(key)
    if (!entry) return undefined
    if (entry.periodoKey !== periodoKey(periodo)) {
      cacheRef.current.delete(key)
      const idx = insertionOrderRef.current.indexOf(key)
      if (idx !== -1) insertionOrderRef.current.splice(idx, 1)
      return undefined
    }
    return entry
  }, [])

  const get = useCallback(<T,>(key: string, periodo: PeriodoBi): T | null => {
    const entry = _resolveEntry(key, periodo)
    return entry ? entry.data as T : null
  }, [_resolveEntry])

  const set = useCallback((key: string, periodo: PeriodoBi, data: unknown) => {
    // Track insertion order (only if it's a new key)
    if (!cacheRef.current.has(key)) {
      insertionOrderRef.current.push(key)
    }
    cacheRef.current.set(key, { data, periodoKey: periodoKey(periodo), timestamp: Date.now() })
    // Evict oldest entries FIFO when over limit
    while (insertionOrderRef.current.length > MAX_ENTRIES) {
      const oldestKey = insertionOrderRef.current.shift()
      if (oldestKey) cacheRef.current.delete(oldestKey)
    }
  }, [])

  const invalidate = useCallback((key: string) => {
    cacheRef.current.delete(key)
    const idx = insertionOrderRef.current.indexOf(key)
    if (idx !== -1) insertionOrderRef.current.splice(idx, 1)
  }, [])

  const clear = useCallback(() => {
    cacheRef.current.clear()
    insertionOrderRef.current = []
  }, [])

  const getTimestamp = useCallback((key: string, periodo: PeriodoBi): number | null => {
    const entry = _resolveEntry(key, periodo)
    return entry ? entry.timestamp : null
  }, [_resolveEntry])

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
