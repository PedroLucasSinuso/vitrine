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

export async function fetchKpis(periodo: PeriodoBi, signal?: AbortSignal): Promise<KpisDTO> {
  const r = await api.get('/bi/kpis', { params: params(periodo), signal })
  return r.data
}

export async function fetchKpisComparativo(periodo: PeriodoBi, signal?: AbortSignal): Promise<KpisComparativoDTO> {
  const r = await api.get('/bi/kpis/comparativo', { params: params(periodo), signal })
  return r.data
}

export async function fetchReceita(periodo: PeriodoBi, dimensao: Dimensao, signal?: AbortSignal): Promise<ItemDimensaoDTO[]> {
  const r = await api.get('/bi/receita', { params: params(periodo, { dimensao }), signal })
  return r.data
}

export async function fetchQuantidade(periodo: PeriodoBi, dimensao: Dimensao, signal?: AbortSignal): Promise<ItemDimensaoDTO[]> {
  const r = await api.get('/bi/quantidade', { params: params(periodo, { dimensao }), signal })
  return r.data
}

export async function fetchCurvaAbc(periodo: PeriodoBi, dimensao: Dimensao, signal?: AbortSignal): Promise<ItemCurvaAbcDTO[]> {
  const r = await api.get('/bi/curva-abc', { params: params(periodo, { dimensao }), signal })
  return r.data
}

export async function fetchRanking(periodo: PeriodoBi, metrica: Metrica, top: number, signal?: AbortSignal): Promise<ItemRankingDTO[]> {
  const r = await api.get('/bi/ranking', { params: params(periodo, { metrica, top }), signal })
  return r.data
}

export async function fetchTrocas(periodo: PeriodoBi, signal?: AbortSignal): Promise<TrocasDTO> {
  const r = await api.get('/bi/trocas', { params: params(periodo), signal })
  return r.data
}

export async function fetchPerdas(periodo: PeriodoBi, signal?: AbortSignal): Promise<MovimentoDTO> {
  const r = await api.get('/bi/perdas', { params: params(periodo), signal })
  return r.data
}

export async function fetchConsumo(periodo: PeriodoBi, signal?: AbortSignal): Promise<MovimentoDTO> {
  const r = await api.get('/bi/consumo', { params: params(periodo), signal })
  return r.data
}

export async function fetchDiario(periodo: PeriodoBi, metrica: Metrica, signal?: AbortSignal): Promise<PontoDiarioDTO[]> {
  const r = await api.get('/bi/diario', { params: params(periodo, { metrica }), signal })
  return r.data
}

export async function fetchDiarioComparativo(periodo: PeriodoBi, metrica: Metrica, signal?: AbortSignal): Promise<DiarioComparativoDTO> {
  const r = await api.get('/bi/diario/comparativo', { params: params(periodo, { metrica }), signal })
  return r.data
}

export async function fetchDiarioProduto(periodo: PeriodoBi, codigo: string, metrica: Metrica, signal?: AbortSignal): Promise<PontoDiarioDTO[]> {
  const r = await api.get('/bi/diario/produto', { params: params(periodo, { codigo, metrica }), signal })
  return r.data
}

export async function fetchTemporalHora(periodo: PeriodoBi, metrica: Metrica, signal?: AbortSignal): Promise<PontoHoraDTO[]> {
  const r = await api.get('/bi/temporal/hora', { params: params(periodo, { metrica }), signal })
  return r.data
}

export async function fetchTemporalDiaSemana(periodo: PeriodoBi, metrica: Metrica, signal?: AbortSignal): Promise<PontoDiaSemanaDTO[]> {
  const r = await api.get('/bi/temporal/dia-semana', { params: params(periodo, { metrica }), signal })
  return r.data
}

export async function fetchSku(periodo: PeriodoBi, codigo: string, signal?: AbortSignal): Promise<SkuDTO> {
  const r = await api.get('/bi/sku', { params: params(periodo, { codigo }), signal })
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
}, signal?: AbortSignal): Promise<TabelaProdutosResponse> {
  const r = await api.get('/bi/tabela-produtos', { params, signal })
  return r.data
}

/**
 * Tenta baixar o PDF do relatório semanal via API.
 * Se falhar (501 — WeasyPrint não disponível), retorna false
 * para que o caller use window.print() como fallback.
 */
export async function exportarPDF(): Promise<boolean> {
  try {
    const r = await api.get('/bi/exportar/pdf', {
      responseType: 'blob',
      timeout: 30000,
    })
    const rawContentType = r.headers['content-type']
    const contentType = typeof rawContentType === 'string' ? rawContentType : ''
    if (!contentType.includes('application/pdf')) {
      // Servidor retornou 501 (ou erro) — conteúdo é JSON
      return false
    }
    const url = URL.createObjectURL(r.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `relatorio_semanal_${new Date().toISOString().slice(0, 10)}.pdf`
    link.click()
    URL.revokeObjectURL(url)
    return true
  } catch {
    return false
  }
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