import api from './client'
import type {
  AliasVendedor, DetalheVendedor, ItemMixVendedor, PontoMensal, ResultadoGrade, MetaVendedor, MetasDaCompetencia, PeriodoBi, PontoSerieVendedor, ResultadoEquipe,
} from '../types'

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

export async function obterMetas(competencia: string): Promise<MetasDaCompetencia> {
  const r = await api.get(`/metas/${competencia}`)
  return r.data
}

export async function salvarMetas(competencia: string, metas: MetaVendedor[]): Promise<MetasDaCompetencia> {
  const r = await api.put(`/metas/${competencia}`, metas)
  return r.data
}

export async function copiarMetas(competencia: string, origem: string): Promise<MetasDaCompetencia> {
  const r = await api.post(`/metas/${competencia}/copiar-de/${origem}`)
  return r.data
}

export async function listarVendedores(): Promise<string[]> {
  const r = await api.get('/vendedores')
  return r.data
}

export async function listarAliases(): Promise<AliasVendedor[]> {
  const r = await api.get('/vendedores/alias')
  return r.data
}

export async function salvarAliases(aliases: AliasVendedor[]): Promise<AliasVendedor[]> {
  const r = await api.put('/vendedores/alias', aliases)
  return r.data
}

export async function fetchGrade(periodo: PeriodoBi, grupo: string, familia: string): Promise<ResultadoGrade> {
  const r = await api.get('/bi/grade', { params: { ...periodo, grupo: grupo || undefined, familia: familia || undefined } })
  return r.data
}

export async function fetchDetalheVendedor(periodo: PeriodoBi, nome: string): Promise<DetalheVendedor> {
  const r = await api.get('/bi/equipe/vendedor', { params: { ...periodo, nome } })
  return r.data
}

export async function fetchSerieMensal(dataFim: string, vendedor?: string, meses = 6): Promise<PontoMensal[]> {
  const r = await api.get('/bi/equipe/serie-mensal', { params: { data_fim: dataFim, meses, vendedor } })
  return r.data
}
