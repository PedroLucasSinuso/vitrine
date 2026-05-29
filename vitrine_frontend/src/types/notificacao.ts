export interface Notificacao {
  id: number
  tipo: 'margem_negativa' | 'sync_erro' | 'sync_lento' | 'encalhe_severo' | 'intelligence_pronto'
  titulo: string
  mensagem: string | null
  dados_json: string | null
  lida: boolean
  resolvida: boolean
  criada_em: string
  lida_em: string | null
  resolvida_em: string | null
}

export interface NotificacaoListResponse {
  notificacoes: Notificacao[]
  total_nao_lidas: number
}

export interface NaoLidasResponse {
  count: number
}

export interface MarcadasResponse {
  marcadas: number
}

export interface RemovidasResponse {
  removidas: number
}
