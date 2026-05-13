import api from './client'

export interface WhatsAppContato {
  id: number
  numero: string
  nome: string
}

export async function listarContatos(): Promise<WhatsAppContato[]> {
  const response = await api.get('/admin/whatsapp/contatos')
  return response.data
}

export async function criarContato(data: { numero: string; nome: string }): Promise<WhatsAppContato> {
  const response = await api.post('/admin/whatsapp/contatos', data)
  return response.data
}

export async function atualizarContato(id: number, data: { numero: string; nome: string }): Promise<WhatsAppContato> {
  const response = await api.put(`/admin/whatsapp/contatos/${id}`, data)
  return response.data
}

export async function removerContato(id: number): Promise<void> {
  await api.delete(`/admin/whatsapp/contatos/${id}`)
}
