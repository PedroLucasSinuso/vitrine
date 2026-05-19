import { useState, useEffect, useRef, useCallback } from 'react'
import AdminHeader from '../components/AdminHeader'
import ListaContatosWhatsApp from '../components/ListaContatosWhatsApp'
import ListaContatosEmail from '../components/ListaContatosEmail'
import PasswordConfigInput from '../components/PasswordConfigInput'
import TestConnectionButton from '../components/TestConnectionButton'
import {
  getConfiguracoes,
  atualizarConfiguracoes,
  uploadLogo,
  testarConexaoErp,
  testarWhatsApp,
  testarEmail,
  testarAnthropic,
  getStatus,
  getCacheStatus,
} from '../api/admin'
import { invalidateConfigCache } from '../stores/configStore'
import { useToast } from '../hooks/useToast'
import {
  Check, Loader2, Database, Mail, MessageSquare, Brain, Settings, Store,
  Activity, RefreshCw, Eye, EyeOff, MapPin, Building2, Clock,
  Key, Globe, Hash, Lock, Send, Calendar, FileText, Upload, Image as ImageIcon,
} from 'lucide-react'

const REPORT_DAYS = [
  { value: 'monday', label: 'Segunda' },
  { value: 'tuesday', label: 'Terça' },
  { value: 'wednesday', label: 'Quarta' },
  { value: 'thursday', label: 'Quinta' },
  { value: 'friday', label: 'Sexta' },
  { value: 'saturday', label: 'Sábado' },
  { value: 'sunday', label: 'Domingo' },
]

const ETL_INTERVALS = [
  { value: '10', label: '10 min' },
  { value: '15', label: '15 min' },
  { value: '30', label: '30 min' },
  { value: '60', label: '1h' },
  { value: '120', label: '2h' },
  { value: '360', label: '6h' },
  { value: '720', label: '12h' },
  { value: '1440', label: '24h' },
]

const ESTADOS_BR = [
  'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
  'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO',
]

const TABS = [
  { id: 'geral', label: 'Geral', icon: Store },
  { id: 'erp', label: 'ERP / Sync', icon: Database },
  { id: 'whatsapp', label: 'WhatsApp', icon: MessageSquare },
  { id: 'email', label: 'E-mail', icon: Mail },
  { id: 'intelligence', label: 'Intelligence', icon: Brain },
  { id: 'sistema', label: 'Sistema', icon: Settings },
]

interface ConfigForm {
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
}

const TEST_WARNING = 'Testa a configuração salva no servidor, não as alterações pendentes'

/* ── Reusable compact input ── */
function CompactInput({
  label, icon: Icon, ...inputProps
}: { label: string; icon?: React.ElementType } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 flex items-center gap-1">
        {Icon && <Icon size={11} className="text-slate-400 dark:text-slate-500" />}
        {label}
      </label>
      <input
        className="w-full border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 rounded-lg px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary transition placeholder:text-slate-300 dark:placeholder:text-slate-600"
        {...inputProps}
      />
    </div>
  )
}

function CompactSelect({
  label, icon: Icon, children, ...selectProps
}: { label: string; icon?: React.ElementType; children: React.ReactNode } & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400 flex items-center gap-1">
        {Icon && <Icon size={11} className="text-slate-400 dark:text-slate-500" />}
        {label}
      </label>
      <select
        className="w-full border border-slate-200 dark:border-slate-700/60 bg-slate-50 dark:bg-slate-800/60 text-slate-800 dark:text-slate-100 rounded-lg px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary transition"
        {...selectProps}
      >
        {children}
      </select>
    </div>
  )
}

function SectionHeader({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description?: string }) {
  return (
    <div className="flex items-start gap-2.5 mb-3">
      <div className="mt-0.5 p-1.5 rounded-lg bg-primary/10 dark:bg-primary/15 text-primary">
        <Icon size={14} />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">{title}</h3>
        {description && <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">{description}</p>}
      </div>
    </div>
  )
}

export default function Configuracoes() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [activeTab, setActiveTab] = useState('geral')
  const [logoPreview, setLogoPreview] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  // System status
  const [statusLastUpdated, setStatusLastUpdated] = useState<string | null>(null)
  const [cacheInfo, setCacheInfo] = useState<{ produtos_cached?: boolean; last_refresh?: string; ttl_seconds?: number } | null>(null)
  const [statusRefreshing, setStatusRefreshing] = useState(false)

  // ERP connection visibility toggle
  const [erpRevealed, setErpRevealed] = useState(false)

  // Form state
  const [form, setForm] = useState<ConfigForm>({})

  useEffect(() => {
    Promise.all([
      getConfiguracoes(),
      getStatus().catch(() => null),
      getCacheStatus().catch(() => null),
    ])
      .then(([configData, statusData, cacheData]) => {
        const c = configData.configuracoes
        setForm(c)
        if (c.logo_url) setLogoPreview(c.logo_url)
        if (statusData) setStatusLastUpdated(statusData.last_updated)
        if (cacheData) setCacheInfo(cacheData)
      })
      .catch(() => toast({ type: 'error', message: 'Erro ao carregar configurações' }))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps -- Mount-only fetch

  async function handleSalvar() {
    setSaving(true)
    setSaved(false)
    try {
      const resp = await atualizarConfiguracoes(form)
      const c = resp.configuracoes
      invalidateConfigCache()
      if (c.logo_url) setLogoPreview(c.logo_url)
      setSaved(true)
      toast({ type: 'success', message: 'Configurações salvas' })
      setTimeout(() => setSaved(false), 2000)
    } catch {
      toast({ type: 'error', message: 'Erro ao salvar configurações' })
    } finally {
      setSaving(false)
    }
  }

  async function handleLogoUpload(file: File) {
    const allowedTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml']
    if (!allowedTypes.includes(file.type)) {
      toast({ type: 'error', message: 'Formato inválido. Use PNG, JPG, WebP ou SVG.' })
      return
    }
    if (file.size > 2 * 1024 * 1024) {
      toast({ type: 'error', message: 'Arquivo muito grande. Máximo: 2MB.' })
      return
    }
    try {
      const result = await uploadLogo(file)
      invalidateConfigCache()
      setLogoPreview(result.logo_url)
      updateField('logo_url', result.logo_url)
      toast({ type: 'success', message: 'Logo atualizada' })
    } catch {
      toast({ type: 'error', message: 'Erro ao fazer upload da logo' })
    }
  }

  function updateField(key: keyof ConfigForm, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const refreshStatus = useCallback(async () => {
    setStatusRefreshing(true)
    try {
      const s = await getStatus()
      setStatusLastUpdated(s.last_updated)
    } catch { /* ignore */ }
    try {
      const c = await getCacheStatus()
      setCacheInfo(c)
    } catch { /* ignore */ }
    finally { setStatusRefreshing(false) }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6 overflow-x-auto">
        <AdminHeader titulo="Configurações" paginaAtual="configuracoes" />
        <div className="flex items-center gap-2 text-sm text-slate-400 dark:text-slate-500 mt-8">
          <Loader2 size={16} className="animate-spin" /> Carregando...
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6 overflow-x-auto">
      <AdminHeader titulo="Configurações" paginaAtual="configuracoes" />

      <div className="w-full max-w-3xl flex flex-col gap-4">

        {/* Tab bar */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-1">
          <div className="flex gap-0.5 overflow-x-auto">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap shrink-0 ${
                  activeTab === id
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/60 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                <Icon size={13} />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm">

          {/* ════════════════════════════════════════════ */}
          {/* ── GERAL ── */}
          {/* ════════════════════════════════════════════ */}
          {activeTab === 'geral' && (
            <div className="p-5 flex flex-col gap-6">

              {/* Branding section */}
              <div>
                <SectionHeader icon={Building2} title="Identidade da loja" description="Nome e logo exibidos no sistema" />
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 ml-9">
                  {/* Logo preview — larger and prominent */}
                  <div className="relative group">
                    <div className="w-24 h-24 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 flex items-center justify-center overflow-hidden">
                      {logoPreview ? (
                        <img src={logoPreview} alt="Logo" className="w-full h-full object-contain rounded-2xl" />
                      ) : (
                        <ImageIcon size={28} className="text-slate-300 dark:text-slate-600" />
                      )}
                    </div>
                    <button
                      onClick={() => fileRef.current?.click()}
                      className="absolute -bottom-1.5 -right-1.5 p-1.5 rounded-full bg-primary text-white shadow-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-primary-hover"
                      title="Trocar logo"
                    >
                      <Upload size={12} />
                    </button>
                    <input
                      ref={fileRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0]
                        if (file) handleLogoUpload(file)
                      }}
                    />
                  </div>

                  {/* Store name */}
                  <div className="flex-1 w-full">
                    <input
                      className="w-full text-lg font-bold text-slate-800 dark:text-slate-100 border-b-2 border-slate-200 dark:border-slate-600 bg-transparent px-1 py-1.5 focus:outline-none focus:border-primary transition placeholder:text-slate-300 dark:placeholder:text-slate-600"
                      value={form.nome_estabelecimento ?? ''}
                      onChange={(e) => updateField('nome_estabelecimento', e.target.value)}
                      placeholder="Nome da sua loja"
                    />
                    <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1 ml-1">
                      Exibido no cabeçalho e nos relatórios
                    </p>
                  </div>
                </div>
              </div>

              {/* Address section */}
              <div>
                <SectionHeader icon={MapPin} title="Endereço" description="Informações de localização do estabelecimento" />
                <div className="ml-9 flex flex-col gap-3">
                  {/* Rua + Número */}
                  <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
                    <CompactInput
                      label="Rua / Logradouro"
                      icon={Globe}
                      value={form.endereco_rua ?? ''}
                      onChange={(e) => updateField('endereco_rua', e.target.value)}
                      placeholder="Av. Brasil"
                    />
                    <CompactInput
                      label="Número"
                      icon={Hash}
                      type="text"
                      value={form.endereco_numero ?? ''}
                      onChange={(e) => updateField('endereco_numero', e.target.value)}
                      placeholder="123"
                      className="max-w-[100px]"
                    />
                  </div>

                  {/* Complemento + Bairro */}
                  <div className="grid grid-cols-1 sm:grid-cols-[1fr_1fr] gap-3">
                    <CompactInput
                      label="Complemento"
                      value={form.endereco_complemento ?? ''}
                      onChange={(e) => updateField('endereco_complemento', e.target.value)}
                      placeholder="Sala 2, Bloco A"
                    />
                    <CompactInput
                      label="Bairro"
                      value={form.endereco_bairro ?? ''}
                      onChange={(e) => updateField('endereco_bairro', e.target.value)}
                      placeholder="Centro"
                    />
                  </div>

                  {/* Cidade + Estado + CEP */}
                  <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_auto] gap-3">
                    <CompactInput
                      label="Cidade"
                      icon={MapPin}
                      value={form.endereco_cidade ?? ''}
                      onChange={(e) => updateField('endereco_cidade', e.target.value)}
                      placeholder="São Paulo"
                    />
                    <CompactSelect
                      label="UF"
                      value={form.endereco_estado ?? ''}
                      onChange={(e) => updateField('endereco_estado', e.target.value)}
                    >
                      <option value="">—</option>
                      {ESTADOS_BR.map((uf) => (
                        <option key={uf} value={uf}>{uf}</option>
                      ))}
                    </CompactSelect>
                    <CompactInput
                      label="CEP"
                      value={form.endereco_cep ?? ''}
                      onChange={(e) => updateField('endereco_cep', e.target.value)}
                      placeholder="01001-000"
                      maxLength={9}
                      className="max-w-[130px]"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════ */}
          {/* ── ERP / SYNC ── */}
          {/* ════════════════════════════════════════════ */}
          {activeTab === 'erp' && (
            <div className="p-5 flex flex-col gap-5">

              {/* Connection — collapsible */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <SectionHeader icon={Database} title="Conexão ERP" description="Credenciais do banco de dados PostgreSQL" />
                  <button
                    onClick={() => setErpRevealed((p) => !p)}
                    className="inline-flex items-center gap-1.5 text-[11px] font-medium text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-700/50 shrink-0"
                  >
                    {erpRevealed ? <EyeOff size={12} /> : <Eye size={12} />}
                    {erpRevealed ? 'Ocultar' : 'Mostrar'}
                  </button>
                </div>

                {erpRevealed && (
                  <div className="ml-9 flex flex-col gap-3 animate-fade-in-up">
                    <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
                      <CompactInput
                        label="Host"
                        icon={Globe}
                        value={form.erp_host ?? ''}
                        onChange={(e) => updateField('erp_host', e.target.value)}
                        placeholder="192.168.1.100"
                      />
                      <CompactInput
                        label="Porta"
                        icon={Hash}
                        type="number"
                        min="1"
                        max="65535"
                        value={form.erp_port ?? '5432'}
                        onChange={(e) => updateField('erp_port', e.target.value)}
                        className="max-w-[90px]"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-[1fr_1fr] gap-3">
                      <CompactInput
                        label="Database"
                        value={form.erp_database ?? ''}
                        onChange={(e) => updateField('erp_database', e.target.value)}
                        placeholder="erp_producao"
                      />
                      <CompactInput
                        label="Usuário"
                        value={form.erp_user ?? ''}
                        onChange={(e) => updateField('erp_user', e.target.value)}
                        placeholder="postgres"
                      />
                    </div>

                    <PasswordConfigInput
                      label="Senha"
                      value={form.erp_password ?? ''}
                      onChange={(v) => updateField('erp_password', v)}
                      placeholder="••••••••"
                    />

                    <TestConnectionButton label="Testar conexão ERP" onTest={testarConexaoErp} warningText={TEST_WARNING} />
                  </div>
                )}

                {!erpRevealed && (
                  <div className="ml-9 text-[11px] text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-700/30 rounded-lg px-3 py-2 flex items-center gap-1.5">
                    <Lock size={11} />
                    Dados de conexão ocultos — clique em "Mostrar" para editar
                  </div>
                )}
              </div>

              {/* Sync settings — always visible */}
              <div className="border-t border-slate-100 dark:border-slate-700/50 pt-4">
                <SectionHeader icon={Clock} title="Agendamento" description="Intervalos de sincronização e cache" />
                <div className="ml-9 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <CompactSelect
                    label="Intervalo ETL"
                    value={form.etl_interval_minutes ?? '60'}
                    onChange={(e) => updateField('etl_interval_minutes', e.target.value)}
                  >
                    {ETL_INTERVALS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </CompactSelect>
                  <CompactInput
                    label="Cache Refresh (min)"
                    icon={RefreshCw}
                    type="number"
                    min="1"
                    value={form.cache_refresh_interval ?? '5'}
                    onChange={(e) => updateField('cache_refresh_interval', e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════ */}
          {/* ── WHATSAPP ── */}
          {/* ════════════════════════════════════════════ */}
          {activeTab === 'whatsapp' && (
            <div className="p-5 flex flex-col gap-5">

              {/* Twilio credentials */}
              <div>
                <SectionHeader icon={MessageSquare} title="Twilio" description="Credenciais para envio via WhatsApp" />
                <div className="ml-9 flex flex-col gap-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <PasswordConfigInput
                      label="Account SID"
                      value={form.twilio_account_sid ?? ''}
                      onChange={(v) => updateField('twilio_account_sid', v)}
                      placeholder="ACxxxxxxxxxxxxxxxx"
                    />
                    <PasswordConfigInput
                      label="Auth Token"
                      value={form.twilio_auth_token ?? ''}
                      onChange={(v) => updateField('twilio_auth_token', v)}
                      placeholder="••••••••"
                    />
                  </div>
                  <PasswordConfigInput
                    label="From Number"
                    value={form.twilio_from_number ?? ''}
                    onChange={(v) => updateField('twilio_from_number', v)}
                    placeholder="whatsapp:+5511999999999"
                  />
                  <TestConnectionButton label="Testar WhatsApp" onTest={testarWhatsApp} warningText={TEST_WARNING} />
                </div>
              </div>

              {/* Weekly report */}
              <div className="border-t border-slate-100 dark:border-slate-700/50 pt-4">
                <SectionHeader icon={FileText} title="Relatório semanal" description="Dia, horário e contatos para envio" />
                <div className="ml-9 flex flex-col gap-3">
                  <div className="flex gap-3 flex-wrap">
                    <CompactSelect
                      label="Dia"
                      icon={Calendar}
                      value={form.report_day ?? 'friday'}
                      onChange={(e) => updateField('report_day', e.target.value)}
                    >
                      {REPORT_DAYS.map((d) => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </CompactSelect>
                    <CompactInput
                      label="Horário"
                      type="time"
                      value={form.report_time ?? '18:00'}
                      onChange={(e) => updateField('report_time', e.target.value)}
                    />
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Contatos</label>
                    <ListaContatosWhatsApp />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════ */}
          {/* ── E-MAIL ── */}
          {/* ════════════════════════════════════════════ */}
          {activeTab === 'email' && (
            <div className="p-5 flex flex-col gap-5">

              {/* SMTP */}
              <div>
                <SectionHeader icon={Mail} title="SMTP" description="Servidor de e-mail para envio de relatórios" />
                <div className="ml-9 flex flex-col gap-3">
                  <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
                    <CompactInput
                      label="Host"
                      icon={Globe}
                      value={form.smtp_host ?? ''}
                      onChange={(e) => updateField('smtp_host', e.target.value)}
                      placeholder="smtp.gmail.com"
                    />
                    <CompactInput
                      label="Porta"
                      icon={Hash}
                      type="number"
                      min="1"
                      value={form.smtp_port ?? '587'}
                      onChange={(e) => updateField('smtp_port', e.target.value)}
                      className="max-w-[90px]"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <CompactInput
                      label="Usuário"
                      value={form.smtp_user ?? ''}
                      onChange={(e) => updateField('smtp_user', e.target.value)}
                      placeholder="email@dominio.com"
                    />
                    <PasswordConfigInput
                      label="Senha"
                      value={form.smtp_password ?? ''}
                      onChange={(v) => updateField('smtp_password', v)}
                      placeholder="••••••••"
                    />
                  </div>

                  <CompactInput
                    label="E-mail remetente"
                    icon={Send}
                    value={form.email_from ?? ''}
                    onChange={(e) => updateField('email_from', e.target.value)}
                    placeholder="relatorios@dominio.com"
                  />

                  <TestConnectionButton label="Testar E-mail" onTest={testarEmail} warningText={TEST_WARNING} />
                </div>
              </div>

              {/* Weekly report */}
              <div className="border-t border-slate-100 dark:border-slate-700/50 pt-4">
                <SectionHeader icon={FileText} title="Relatório semanal" description="Dia, horário e contatos para envio" />
                <div className="ml-9 flex flex-col gap-3">
                  <div className="flex gap-3 flex-wrap">
                    <CompactSelect
                      label="Dia"
                      icon={Calendar}
                      value={form.report_email_day ?? 'friday'}
                      onChange={(e) => updateField('report_email_day', e.target.value)}
                    >
                      {REPORT_DAYS.map((d) => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </CompactSelect>
                    <CompactInput
                      label="Horário"
                      type="time"
                      value={form.report_email_time ?? '18:00'}
                      onChange={(e) => updateField('report_email_time', e.target.value)}
                    />
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Contatos</label>
                    <ListaContatosEmail />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ════════════════════════════════════════════ */}
          {/* ── INTELLIGENCE ── */}
          {/* ════════════════════════════════════════════ */}
          {activeTab === 'intelligence' && (
            <div className="p-5 flex flex-col gap-5">

              <div>
                <SectionHeader icon={Key} title="API Keys" description="Chaves dos provedores de IA para relatórios inteligentes" />
                <div className="ml-9 flex flex-col gap-3">
                  <PasswordConfigInput
                    label="Anthropic API Key"
                    value={form.anthropic_api_key ?? ''}
                    onChange={(v) => updateField('anthropic_api_key', v)}
                    placeholder="sk-ant-xxxxxxxxxxxxxxxx"
                  />
                  <PasswordConfigInput
                    label="OpenAI API Key"
                    value={form.openai_api_key ?? ''}
                    onChange={(v) => updateField('openai_api_key', v)}
                    placeholder="sk-xxxxxxxxxxxxxxxx"
                  />
                </div>
              </div>

              <div className="border-t border-slate-100 dark:border-slate-700/50 pt-4">
                <SectionHeader icon={Clock} title="Relatório" description="Período de análise dos dados" />
                <div className="ml-9">
                  <CompactInput
                    label="Dias retroativos"
                    type="number"
                    min="1"
                    value={form.relatorio_dias_retroativos ?? '30'}
                    onChange={(e) => updateField('relatorio_dias_retroativos', e.target.value)}
                    placeholder="30"
                    className="max-w-[120px]"
                  />
                  <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">Quantos dias de dados o relatório de inteligência analisa</p>
                </div>
              </div>

              <TestConnectionButton label="Testar Anthropic" onTest={testarAnthropic} warningText={TEST_WARNING} />
            </div>
          )}

          {/* ════════════════════════════════════════════ */}
          {/* ── SISTEMA ── */}
          {/* ════════════════════════════════════════════ */}
          {activeTab === 'sistema' && (
            <div className="p-5 flex flex-col gap-5">

              <div>
                <SectionHeader icon={Activity} title="Status do sistema" description="Informações de sincronização e cache" />
                <div className="ml-9 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Last ETL sync */}
                  <div className="rounded-xl border border-slate-200 dark:border-slate-700/50 bg-slate-50 dark:bg-slate-700/30 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="p-1 rounded-md bg-emerald-500/10 text-emerald-500">
                        <Activity size={12} />
                      </div>
                      <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Última sincronia ETL</span>
                    </div>
                    <p className="text-sm font-mono text-slate-700 dark:text-slate-200">
                      {statusLastUpdated
                        ? new Date(statusLastUpdated).toLocaleString('pt-BR', {
                            day: '2-digit', month: '2-digit', year: 'numeric',
                            hour: '2-digit', minute: '2-digit',
                          })
                        : '—'}
                    </p>
                  </div>

                  {/* Cache info — dados reais do backend */}
                  <div className="rounded-xl border border-slate-200 dark:border-slate-700/50 bg-slate-50 dark:bg-slate-700/30 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`p-1 rounded-md ${cacheInfo?.produtos_cached ? 'bg-emerald-500/10 text-emerald-500' : 'bg-amber-500/10 text-amber-500'}`}>
                        <Database size={12} />
                      </div>
                      <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Cache</span>
                    </div>
                    {cacheInfo ? (
                      <div className="text-xs text-slate-600 dark:text-slate-300 space-y-1">
                        <p>
                          <span className="text-slate-400">Status: </span>
                          <span className={cacheInfo.produtos_cached ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}>
                            {cacheInfo.produtos_cached ? 'Ativo' : 'Vazio'}
                          </span>
                        </p>
                        {cacheInfo.last_refresh && (
                          <p>
                            <span className="text-slate-400">Última atualização: </span>
                            {new Date(cacheInfo.last_refresh).toLocaleString('pt-BR')}
                          </p>
                        )}
                        {cacheInfo.ttl_seconds != null && (
                          <p>
                            <span className="text-slate-400">TTL: </span>
                            {cacheInfo.ttl_seconds}s
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">—</p>
                    )}
                  </div>
                </div>
              </div>

              <button
                onClick={refreshStatus}
                disabled={statusRefreshing}
                className="ml-9 inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary-hover disabled:opacity-50 transition px-3 py-1.5 rounded-lg hover:bg-primary/5 w-fit"
              >
                {statusRefreshing ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                Atualizar status
              </button>
            </div>
          )}
        </div>

        {/* Save bar */}
        <div className="flex items-center justify-center gap-3 py-2">
          <button
            onClick={handleSalvar}
            disabled={saving}
            className={`inline-flex items-center gap-2 font-semibold px-8 py-2.5 rounded-xl transition disabled:opacity-50 text-sm ${
              saved
                ? 'bg-emerald-500 text-white'
                : 'bg-primary hover:bg-primary-hover text-white shadow-sm hover:shadow'
            }`}
          >
            {saved ? <Check size={15} /> : null}
            {saving ? 'Salvando...' : saved ? 'Salvo!' : 'Salvar configurações'}
          </button>
        </div>

      </div>
    </div>
  )
}
