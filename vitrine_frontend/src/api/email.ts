import api from './client'

export interface EmailContato {
  id: number
  email: string
  nome: string
}

export async function listarContatosEmail(): Promise<EmailContato[]> {
  const response = await api.get('/admin/email/contatos')
  return response.data
}

export async function criarContatoEmail(data: { email: string; nome: string }): Promise<EmailContato> {
  const response = await api.post('/admin/email/contatos', data)
  return response.data
}

export async function atualizarContatoEmail(id: number, data: { email: string; nome: string }): Promise<EmailContato> {
  const response = await api.put(`/admin/email/contatos/${id}`, data)
  return response.data
}

export async function removerContatoEmail(id: number): Promise<void> {
  await api.delete(`/admin/email/contatos/${id}`)
}
