import api from './client'
import type { ItemMixVendedor, PeriodoBi, PontoSerieVendedor, ResultadoEquipe } from '../types'

export async function fetchEquipe(periodo: PeriodoBi): Promise<ResultadoEquipe> {
  const r = await api.get('/bi/equipe', { params: periodo })
  return r.data
}

function paramsVendedor(periodo: PeriodoBi, vendedor: string | null) {
  return vendedor === null ? { ...periodo } : { ...periodo, vendedor }
}

export async function fetchSerieVendedor(periodo: PeriodoBi, vendedor: string | null): Promise<PontoSerieVendedor[]> {
  const r = await api.get('/bi/equipe/serie', { params: paramsVendedor(periodo, vendedor) })
  return r.data
}

export async function fetchMixVendedor(periodo: PeriodoBi, vendedor: string | null): Promise<ItemMixVendedor[]> {
  const r = await api.get('/bi/equipe/mix', { params: paramsVendedor(periodo, vendedor) })
  return r.data
}
