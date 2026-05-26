import api from './client'
import type {
  KpisDTO, KpisComparativoDTO, ItemDimensaoDTO, ItemCurvaAbcDTO, ItemRankingDTO,
  TrocasDTO, MovimentoDTO, PontoDiarioDTO, PontoHoraDTO,
  PontoDiaSemanaDTO, SkuDTO, DiarioComparativoDTO, Dimensao, Metrica, PeriodoBi,
  TabelaProdutosResponse, SortByProduto,
} from '../types'

const MAX_BI_DAYS = 180

function params(periodo: PeriodoBi, extra?: Record<string, unknown>) {
  const dataInicio = new Date(periodo.data_inicio + 'T00:00:00')
  const dataFim = new Date(periodo.data_fim + 'T00:00:00')
  const diffDays = Math.round((dataFim.getTime() - dataInicio.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays > MAX_BI_DAYS) {
    const clamped = new Date(dataInicio)
    clamped.setDate(clamped.getDate() + MAX_BI_DAYS)
    const clampedStr = clamped.toISOString().split('T')[0]
    console.warn(
      `[BI] Período de ${diffDays} dias excede o máximo de ${MAX_BI_DAYS}. ` +
      `data_fim ajustado de ${periodo.data_fim} para ${clampedStr}`
    )
    return { data_inicio: periodo.data_inicio, data_fim: clampedStr, ...extra }
  }
  return { data_inicio: periodo.data_inicio, data_fim: periodo.data_fim, ...extra }
}

export async function fetchKpis(periodo: PeriodoBi): Promise<KpisDTO> {
  const r = await api.get('/bi/kpis', { params: params(periodo) })
  return r.data
}

export async function fetchKpisComparativo(periodo: PeriodoBi): Promise<KpisComparativoDTO> {
  const r = await api.get('/bi/kpis/comparativo', { params: params(periodo) })
  return r.data
}

export async function fetchReceita(periodo: PeriodoBi, dimensao: Dimensao): Promise<ItemDimensaoDTO[]> {
  const r = await api.get('/bi/receita', { params: params(periodo, { dimensao }) })
  return r.data
}

export async function fetchQuantidade(periodo: PeriodoBi, dimensao: Dimensao): Promise<ItemDimensaoDTO[]> {
  const r = await api.get('/bi/quantidade', { params: params(periodo, { dimensao }) })
  return r.data
}

export async function fetchCurvaAbc(periodo: PeriodoBi, dimensao: Dimensao): Promise<ItemCurvaAbcDTO[]> {
  const r = await api.get('/bi/curva-abc', { params: params(periodo, { dimensao }) })
  return r.data
}

export async function fetchRanking(periodo: PeriodoBi, metrica: Metrica, top: number): Promise<ItemRankingDTO[]> {
  const r = await api.get('/bi/ranking', { params: params(periodo, { metrica, top }) })
  return r.data
}

export async function fetchTrocas(periodo: PeriodoBi): Promise<TrocasDTO> {
  const r = await api.get('/bi/trocas', { params: params(periodo) })
  return r.data
}

export async function fetchPerdas(periodo: PeriodoBi): Promise<MovimentoDTO> {
  const r = await api.get('/bi/perdas', { params: params(periodo) })
  return r.data
}

export async function fetchConsumo(periodo: PeriodoBi): Promise<MovimentoDTO> {
  const r = await api.get('/bi/consumo', { params: params(periodo) })
  return r.data
}

export async function fetchDiario(periodo: PeriodoBi, metrica: Metrica): Promise<PontoDiarioDTO[]> {
  const r = await api.get('/bi/diario', { params: params(periodo, { metrica }) })
  return r.data
}

export async function fetchDiarioComparativo(periodo: PeriodoBi, metrica: Metrica): Promise<DiarioComparativoDTO> {
  const r = await api.get('/bi/diario/comparativo', { params: params(periodo, { metrica }) })
  return r.data
}

export async function fetchDiarioProduto(periodo: PeriodoBi, codigo: string, metrica: Metrica): Promise<PontoDiarioDTO[]> {
  const r = await api.get('/bi/diario/produto', { params: params(periodo, { codigo, metrica }) })
  return r.data
}

export async function fetchTemporalHora(periodo: PeriodoBi, metrica: Metrica): Promise<PontoHoraDTO[]> {
  const r = await api.get('/bi/temporal/hora', { params: params(periodo, { metrica }) })
  return r.data
}

export async function fetchTemporalDiaSemana(periodo: PeriodoBi, metrica: Metrica): Promise<PontoDiaSemanaDTO[]> {
  const r = await api.get('/bi/temporal/dia-semana', { params: params(periodo, { metrica }) })
  return r.data
}

export async function fetchSku(periodo: PeriodoBi, codigo: string): Promise<SkuDTO> {
  const r = await api.get('/bi/sku', { params: params(periodo, { codigo }) })
  return r.data
}

export async function fetchTabelaProdutos(params: {
  grupo?: string
  familia?: string
  search?: string
  sort_by?: SortByProduto
  sort_order?: string
  limit?: number
  offset?: number
}): Promise<TabelaProdutosResponse> {
  const r = await api.get('/bi/tabela-produtos', { params })
  return r.data
}

export async function exportarExcelBI(
  periodo: PeriodoBi,
  relatorio: string,
  extra?: Record<string, unknown>,
): Promise<void> {
  const r = await api.get('/bi/exportar/excel', {
    params: { ...params(periodo), relatorio, ...extra },
    responseType: 'blob',
  })

  // ── Verifica se a resposta é JSON de erro (ex: 500 com corpo JSON) ──
  const rawContentType = r.headers['content-type']
  const contentType = typeof rawContentType === 'string' ? rawContentType : ''
  if (contentType.includes('application/json')) {
    // Resposta inesperada: tenta ler o JSON para extrair mensagem de erro
    const text = await r.data.text()
    try {
      const err = JSON.parse(text)
      throw new Error(err.detail ?? err.message ?? 'Erro ao exportar Excel')
    } catch {
      throw new Error('Erro ao exportar Excel')
    }
  }

  const url = URL.createObjectURL(r.data)
  const link = document.createElement('a')
  link.href = url
  link.download = `bi_${relatorio}_${periodo.data_inicio}_${periodo.data_fim}.xlsx`
  link.click()
  URL.revokeObjectURL(url)
}