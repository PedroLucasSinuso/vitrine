import api from './client'
import type { NotificacaoListResponse, NaoLidasResponse, MarcadasResponse, RemovidasResponse } from '../types/notificacao'

export async function fetchNotificacoes(limit = 50, offset = 0): Promise<NotificacaoListResponse> {
  const { data } = await api.get('/notificacoes', { params: { limit, offset } })
  return data
}

export async function fetchNaoLidas(): Promise<NaoLidasResponse> {
  const { data } = await api.get('/notificacoes/nao-lidas')
  return data
}

export async function marcarComoLida(id: number): Promise<void> {
  await api.patch(`/notificacoes/${id}/ler`)
}

export async function marcarTodasComoLidas(): Promise<MarcadasResponse> {
  const { data } = await api.post('/notificacoes/ler-todas')
  return data
}

export async function limparNotificacoes(dias = 30): Promise<RemovidasResponse> {
  const { data } = await api.post('/notificacoes/limpar', null, { params: { dias } })
  return data
}
