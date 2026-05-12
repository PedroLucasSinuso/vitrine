export interface SyncJob {
  job_id: string
  started_at: string
  finished_at: string | null
  status: 'sucesso' | 'em_progresso' | 'erro' | 'started'
  produtos_count: number | null
  codigos_count: number | null
  error_message: string | null
}

export interface SyncHistory {
  jobs: SyncJob[]
  total: number
}