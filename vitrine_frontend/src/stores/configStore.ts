import { getConfiguracoes } from '../api/admin'

interface ConfigCache {
  marketName: string
  marketLogoUrl: string
}

let _cache: ConfigCache | null = null

export async function getConfigsCache(): Promise<ConfigCache> {
  if (_cache) return _cache

  const ls = localStorage.getItem('vitrine_config')
  if (ls) {
    try {
      _cache = JSON.parse(ls) as ConfigCache
      return _cache
    } catch {
      localStorage.removeItem('vitrine_config')
    }
  }

  const data = await getConfiguracoes()
  const c = data.configuracoes
  _cache = {
    marketName: c.market_name ?? '',
    marketLogoUrl: c.logo_url ?? '',
  }
  localStorage.setItem('vitrine_config', JSON.stringify(_cache))
  if (c.market_name) localStorage.setItem('app_marketName', c.market_name)
  if (c.logo_url) localStorage.setItem('app_marketLogoUrl', c.logo_url)
  return _cache
}

export function invalidateConfigCache(): void {
  _cache = null
  localStorage.removeItem('vitrine_config')
}
