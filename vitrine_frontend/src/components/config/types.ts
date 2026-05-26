/* ── Tipos e constantes compartilhadas entre as abas de Configurações ── */

export interface ConfigForm {
  [key: string]: string | undefined
  nome_estabelecimento?: string
  logo_url?: string
  endereco_rua?: string
  endereco_numero?: string
  endereco_complemento?: string
  endereco_bairro?: string
  endereco_cidade?: string
  endereco_estado?: string
  endereco_cep?: string
  erp_host?: string
  erp_port?: string
  erp_database?: string
  erp_user?: string
  erp_password?: string
  etl_interval_minutes?: string
  cache_refresh_interval?: string
  twilio_account_sid?: string
  twilio_auth_token?: string
  twilio_from_number?: string
  report_day?: string
  report_time?: string
  smtp_host?: string
  smtp_port?: string
  smtp_user?: string
  smtp_password?: string
  report_email_day?: string
  report_email_time?: string
  email_from?: string
  anthropic_api_key?: string
  openai_api_key?: string
  relatorio_dias_retroativos?: string
  meta_faturamento_mensal?: string
}

export interface TabProps {
  form: ConfigForm
  updateField: (key: string, value: string) => void
}

export const REPORT_DAYS = [
  { value: 'monday', label: 'Segunda' },
  { value: 'tuesday', label: 'Terça' },
  { value: 'wednesday', label: 'Quarta' },
  { value: 'thursday', label: 'Quinta' },
  { value: 'friday', label: 'Sexta' },
  { value: 'saturday', label: 'Sábado' },
  { value: 'sunday', label: 'Domingo' },
]

export const ETL_INTERVALS = [
  { value: '10', label: '10 min' },
  { value: '15', label: '15 min' },
  { value: '30', label: '30 min' },
  { value: '60', label: '1h' },
  { value: '120', label: '2h' },
  { value: '360', label: '6h' },
  { value: '720', label: '12h' },
  { value: '1440', label: '24h' },
]

export const ESTADOS_BR = [
  'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
  'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO',
]
