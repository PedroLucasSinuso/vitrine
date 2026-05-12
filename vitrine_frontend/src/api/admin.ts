import api from './client'
import type { SyncJob, SyncHistory } from '../types'

export async function triggerSync(): Promise<{ job_id: number }> {
  const response = await api.post('/admin/sync')
  return response.data
}

export async function getSyncStatus(jobId: number, signal?: AbortSignal): Promise<SyncJob> {
  const response = await api.get(`/admin/sync/${jobId}`, { signal })
  return response.data
}

export async function getSyncHistory(limit = 10): Promise<SyncHistory> {
  const response = await api.get('/admin/sync', { params: { limit } })
  return response.data
}

export async function getConfiguracoes(): Promise<{ configuracoes: Record<string, string> }> {
  const response = await api.get('/admin/configuracoes')
  return response.data
}

export async function atualizarConfiguracoes(
  valores: Record<string, string>
): Promise<{ configuracoes: Record<string, string> }> {
  const response = await api.patch('/admin/configuracoes', { valores })
  return response.data
}

export async function uploadLogo(file: File): Promise<{ logo_url: string }> {
  const form = new FormData()
  form.append('file', file)
  const response = await api.post('/admin/configuracoes/logo', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

import type { SessaoInventario, ItemInventario, ItemInventarioSubmit } from '../types/inventario'

export async function getSessoesInventario(): Promise<SessaoInventario[]> {
  const response = await api.get('/admin/inventario/sessoes')
  return response.data
}

export async function criarSessaoInventario(nome: string): Promise<SessaoInventario> {
  const response = await api.post('/admin/inventario/sessoes', { nome })
  return response.data
}

export async function entrarSessaoInventario(codigoConvite: string): Promise<SessaoInventario> {
  const response = await api.post('/admin/inventario/sessoes/entrar', { codigo_convite: codigoConvite })
  return response.data
}

export async function encerrarSessaoInventario(sessaoId: number): Promise<void> {
  await api.patch(`/admin/inventario/sessoes/${sessaoId}`)
}

export async function getItensInventario(sessaoId: number, consolidado?: boolean): Promise<ItemInventario[]> {
  const response = await api.get(`/admin/inventario/sessoes/${sessaoId}/itens`, { params: { consolidado } })
  return response.data
}

export async function adicionarItemInventario(sessaoId: number, item: ItemInventarioSubmit): Promise<void> {
  await api.post(`/admin/inventario/sessoes/${sessaoId}/itens`, item)
}

export async function atualizarItemInventario(sessaoId: number, codigo: string, quantidade: number): Promise<void> {
  await api.patch(`/admin/inventario/sessoes/${sessaoId}/itens/${encodeURIComponent(codigo)}`, { quantidade })
}

export async function limparItensInventario(sessaoId: number): Promise<void> {
  await api.delete(`/admin/inventario/sessoes/${sessaoId}/itens`)
}

export async function getConsolidadoGeral(): Promise<ItemInventario[]> {
  const response = await api.get('/admin/inventario/consolidado-geral')
  return response.data
}
