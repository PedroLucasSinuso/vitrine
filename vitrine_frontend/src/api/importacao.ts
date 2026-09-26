import api from './client'
import type { CampoDataset, DatasetResumo, Importacao, ImportacaoResumo, Mapeamento, TipoDataset } from '../types'

export async function enviarArquivo(arquivo: File): Promise<Importacao> {
  const dados = new FormData()
  dados.append('arquivo', arquivo)
  const r = await api.post('/importacoes', dados)
  return r.data
}

export async function listarImportacoes(): Promise<ImportacaoResumo[]> {
  const r = await api.get('/importacoes')
  return r.data
}

export async function obterImportacao(id: number): Promise<Importacao> {
  const r = await api.get(`/importacoes/${id}`)
  return r.data
}

export async function salvarMapeamento(id: number, mapeamento: Mapeamento): Promise<Importacao> {
  const r = await api.put(`/importacoes/${id}/mapeamento`, mapeamento)
  return r.data
}

export async function confirmarImportacao(id: number): Promise<DatasetResumo> {
  const r = await api.post(`/importacoes/${id}/confirmar`)
  return r.data
}

export async function listarCampos(): Promise<Record<TipoDataset, CampoDataset[]>> {
  const r = await api.get('/importacoes/campos')
  return r.data
}

export async function listarDatasets(): Promise<DatasetResumo[]> {
  const r = await api.get('/datasets')
  return r.data
}

export async function excluirDataset(id: number): Promise<void> {
  await api.delete(`/datasets/${id}`)
}

export async function baixarRelatorioExemplo(): Promise<{ nome: string; conteudo: Blob }> {
  const r = await api.get('/importacoes/exemplo', { responseType: 'blob' })
  const disposicao = String(r.headers['content-disposition'] ?? '')
  const nome = /filename="([^"]+)"/.exec(disposicao)?.[1] ?? 'relatorio-exemplo.xlsx'
  return { nome, conteudo: r.data }
}
