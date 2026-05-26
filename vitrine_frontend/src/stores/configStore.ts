import { getConfiguracoes } from '../api/admin'

interface ConfigCache {
  marketName: string
  marketLogoUrl: string
  meta_faturamento_mensal?: string
}

const CACHE_TTL_MS = 30_000

let _cache: ConfigCache | null = null
let _cacheTimestamp = 0
let pendingPromise: Promise<ConfigCache> | null = null

export async function getConfigsCache(): Promise<ConfigCache> {
  const now = Date.now()
  if (_cache && now - _cacheTimestamp < CACHE_TTL_MS) return _cache

  const ls = localStorage.getItem('vitrine_config')
  if (ls) {
    try {
      _cache = JSON.parse(ls) as ConfigCache
      _cacheTimestamp = now
      return _cache
    } catch {
      localStorage.removeItem('vitrine_config')
    }
  }

  // Se já há uma requisição em andamento, aguarda ela em vez de disparar outra
  if (pendingPromise) return pendingPromise

  pendingPromise = getConfiguracoes()
    .then((data) => {
      const c = data.configuracoes
      _cache = {
        marketName: c.market_name ?? '',
        marketLogoUrl: c.logo_url ?? '',
        meta_faturamento_mensal: c.meta_faturamento_mensal ?? undefined,
      }
      _cacheTimestamp = Date.now()
      localStorage.setItem('vitrine_config', JSON.stringify(_cache))
      if (c.market_name) localStorage.setItem('app_marketName', c.market_name)
      if (c.logo_url) localStorage.setItem('app_marketLogoUrl', c.logo_url)
      return _cache
    })
    .catch((err) => {
      // Fallback para localStorage em caso de erro na API
      const cached = localStorage.getItem('vitrine_config')
      if (cached) {
        try {
          _cache = JSON.parse(cached) as ConfigCache
          _cacheTimestamp = Date.now()
          return _cache
        } catch {
          /* ignore - fall through to re-throw */
        }
      }
      throw err
    })
    .finally(() => {
      pendingPromise = null
    })

  return pendingPromise
}

export function invalidateConfigCache(): void {
  _cache = null
  _cacheTimestamp = 0
  localStorage.removeItem('vitrine_config')
}

/** Force reload config from server, bypassing cache and localStorage. */
export async function refreshConfig(): Promise<ConfigCache> {
  _cache = null
  _cacheTimestamp = 0
  localStorage.removeItem('vitrine_config')
  return getConfigsCache()
}
