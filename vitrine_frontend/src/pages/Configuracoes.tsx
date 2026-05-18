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
  getStatus,
  getCacheStatus,
} from '../api/admin'
import { invalidateConfigCache } from '../stores/configStore'
import { useToast } from '../hooks/useToast'
import { Check, Loader2, Database, Mail, MessageSquare, Brain, Settings, Store, Activity, RefreshCw } from 'lucide-react'

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
  { value: '10', label: '10 minutos' },
  { value: '15', label: '15 minutos' },
  { value: '30', label: '30 minutos' },
  { value: '60', label: '1 hora' },
  { value: '120', label: '2 horas' },
  { value: '360', label: '6 horas' },
  { value: '720', label: '12 horas' },
  { value: '1440', label: '24 horas' },
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
  market_name?: string
  cidade?: string
  logo_url?: string
  erp_postgres_url?: string
  etl_interval_minutes?: string
  cache_refresh_interval?: string
  twilio_account_sid?: string
  twilio_auth_token?: string
  report_day?: string
  report_time?: string
  smtp_server?: string
  smtp_port?: string
  smtp_user?: string
  smtp_password?: string
  report_email_day?: string
  report_email_time?: string
  anthropic_api_key?: string
  [key: string]: string | undefined
}

const TEST_WARNING = 'Testa a configuração salva no servidor, não as alterações pendentes'

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
  const [cacheInfo, setCacheInfo] = useState<Record<string, unknown> | null>(null)

  // Form state — all config keys
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
        if (c.market_name) localStorage.setItem('app_marketName', c.market_name)
        if (c.logo_url) localStorage.setItem('app_marketLogoUrl', c.logo_url)
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
      // Send all fields — backend handles "***configurado***" as preserve
      const resp = await atualizarConfiguracoes(form)
      const c = resp.configuracoes
      invalidateConfigCache()
      if (c.market_name) localStorage.setItem('app_marketName', c.market_name)
      if (c.logo_url) { localStorage.setItem('app_marketLogoUrl', c.logo_url); setLogoPreview(c.logo_url) }
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
      localStorage.setItem('app_marketLogoUrl', result.logo_url)
      toast({ type: 'success', message: 'Logo atualizada' })
    } catch {
      toast({ type: 'error', message: 'Erro ao fazer upload da logo' })
    }
  }

  function updateField(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const refreshStatus = useCallback(async () => {
    try {
      const s = await getStatus()
      setStatusLastUpdated(s.last_updated)
    } catch { /* ignore */ }
    try {
      const c = await getCacheStatus()
      setCacheInfo(c)
    } catch { /* ignore */ }
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6 overflow-x-hidden">
        <AdminHeader titulo="Configurações" paginaAtual="configuracoes" />
        <div className="flex items-center gap-2 text-sm text-slate-400 dark:text-slate-500 mt-8">
          <Loader2 size={16} className="animate-spin" /> Carregando...
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center px-4 py-6 overflow-x-hidden">
      <AdminHeader titulo="Configurações" paginaAtual="configuracoes" />

      <div className="w-full max-w-4xl flex flex-col gap-5">

        {/* Tab bar */}
        <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/50 shadow-sm p-1.5">
          <div className="flex gap-1 overflow-x-auto">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition whitespace-nowrap shrink-0 ${
                  activeTab === id
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-700 dark:hover:text-slate-200'
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

          {/* ── GERAL ── */}
          {activeTab === 'geral' && (
            <div className="p-5 flex flex-col gap-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Nome da loja</label>
                  <input
                    className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
                    value={form.market_name ?? ''}
                    onChange={(e) => updateField('market_name', e.target.value)}
                    placeholder="Ex: Supermercado Vitória"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Cidade</label>
                  <input
                    className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
                    value={form.cidade ?? ''}
                    onChange={(e) => updateField('cidade', e.target.value)}
                    placeholder="Ex: São Paulo - SP"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Logo</label>
                <div className="flex items-center gap-3">
                  {logoPreview ? (
                    <img src={logoPreview} alt="Logo" className="h-8 w-auto rounded-lg border border-slate-200 dark:border-slate-700" />
                  ) : (
                    <div className="h-8 w-8 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-400 dark:text-slate-500 text-[10px]">
                      —
                    </div>
                  )}
                  <button
                    onClick={() => fileRef.current?.click()}
                    className="text-xs text-primary hover:text-primary-hover font-medium transition"
                  >
                    {logoPreview ? 'Trocar logo' : 'Fazer upload'}
                  </button>
                </div>
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
            </div>
          )}

          {/* ── ERP / SYNC ── */}
          {activeTab === 'erp' && (
            <div className="p-5 flex flex-col gap-5">
              <PasswordConfigInput
                label="PostgreSQL Connection String"
                value={form.erp_postgres_url ?? ''}
                onChange={(v) => updateField('erp_postgres_url', v)}
                placeholder="postgresql://user:pass@host:5432/db"
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Intervalo ETL</label>
                  <select
                    className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
                    value={form.etl_interval_minutes ?? '60'}
                    onChange={(e) => updateField('etl_interval_minutes', e.target.value)}
                  >
                    {ETL_INTERVALS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Cache Refresh (minutos)</label>
                  <input
                    type="number"
                    min="1"
                    className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition max-w-xs"
                    value={form.cache_refresh_interval ?? '5'}
                    onChange={(e) => updateField('cache_refresh_interval', e.target.value)}
                  />
                </div>
              </div>

              <TestConnectionButton label="Testar conexão ERP" onTest={testarConexaoErp} warningText={TEST_WARNING} />
            </div>
          )}

          {/* ── WHATSAPP ── */}
          {activeTab === 'whatsapp' && (
            <div className="p-5 flex flex-col gap-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <PasswordConfigInput
                  label="Twilio Account SID"
                  value={form.twilio_account_sid ?? ''}
                  onChange={(v) => updateField('twilio_account_sid', v)}
                  placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                />
                <PasswordConfigInput
                  label="Twilio Auth Token"
                  value={form.twilio_auth_token ?? ''}
                  onChange={(v) => updateField('twilio_auth_token', v)}
                  placeholder="••••••••••••••••"
                />
              </div>

              <div className="border-t border-slate-100 dark:border-slate-700/50 pt-5">
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">Relatório Semanal</h3>
                <div className="flex gap-4 flex-wrap mb-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Dia da semana</label>
                    <select
                      className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
                      value={form.report_day ?? 'friday'}
                      onChange={(e) => updateField('report_day', e.target.value)}
                    >
                      {REPORT_DAYS.map((d) => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Horário</label>
                    <input
                      type="time"
                      className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
                      value={form.report_time ?? '18:00'}
                      onChange={(e) => updateField('report_time', e.target.value)}
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Contatos</label>
                  <ListaContatosWhatsApp />
                </div>
              </div>

              <TestConnectionButton label="Testar WhatsApp" onTest={testarWhatsApp} warningText={TEST_WARNING} />
            </div>
          )}

          {/* ── E-MAIL ── */}
          {activeTab === 'email' && (
            <div className="p-5 flex flex-col gap-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">SMTP Server</label>
                  <input
                    className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
                    value={form.smtp_server ?? ''}
                    onChange={(e) => updateField('smtp_server', e.target.value)}
                    placeholder="smtp.gmail.com"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">SMTP Port</label>
                  <input
                    type="number"
                    min="1"
                    className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition max-w-xs"
                    value={form.smtp_port ?? '587'}
                    onChange={(e) => updateField('smtp_port', e.target.value)}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">SMTP User</label>
                  <input
                    className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
                    value={form.smtp_user ?? ''}
                    onChange={(e) => updateField('smtp_user', e.target.value)}
                    placeholder="email@dominio.com"
                  />
                </div>
                <PasswordConfigInput
                  label="SMTP Password"
                  value={form.smtp_password ?? ''}
                  onChange={(v) => updateField('smtp_password', v)}
                  placeholder="••••••••"
                />
              </div>

              <div className="border-t border-slate-100 dark:border-slate-700/50 pt-5">
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">Relatório Semanal</h3>
                <div className="flex gap-4 flex-wrap mb-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Dia da semana</label>
                    <select
                      className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
                      value={form.report_email_day ?? 'friday'}
                      onChange={(e) => updateField('report_email_day', e.target.value)}
                    >
                      {REPORT_DAYS.map((d) => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Horário</label>
                    <input
                      type="time"
                      className="border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary focus:border-transparent transition"
                      value={form.report_email_time ?? '18:00'}
                      onChange={(e) => updateField('report_email_time', e.target.value)}
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Contatos</label>
                  <ListaContatosEmail />
                </div>
              </div>

              <TestConnectionButton label="Testar E-mail" onTest={testarEmail} warningText={TEST_WARNING} />
            </div>
          )}

          {/* ── INTELLIGENCE ── */}
          {activeTab === 'intelligence' && (
            <div className="p-5 flex flex-col gap-5">
              <PasswordConfigInput
                label="Anthropic API Key"
                value={form.anthropic_api_key ?? ''}
                onChange={(v) => updateField('anthropic_api_key', v)}
                placeholder="sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
              />

              <div className="flex items-center gap-2 text-xs text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-700/50 rounded-lg px-3 py-2">
                <Brain size={13} />
                Teste de conexão com Anthropic será implementado em breve.
              </div>
            </div>
          )}

          {/* ── SISTEMA ── */}
          {activeTab === 'sistema' && (
            <div className="p-5 flex flex-col gap-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Activity size={14} className="text-primary" />
                    <h3 className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wide">Última Sincronia ETL</h3>
                  </div>
                  <p className="text-sm text-slate-800 dark:text-slate-100 font-mono">
                    {statusLastUpdated ? new Date(statusLastUpdated).toLocaleString('pt-BR') : '—'}
                  </p>
                </div>

                <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Database size={14} className="text-primary" />
                    <h3 className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wide">Status do Cache</h3>
                  </div>
                  {cacheInfo ? (
                    <pre className="text-xs text-slate-600 dark:text-slate-300 font-mono overflow-x-auto">
                      {JSON.stringify(cacheInfo, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-sm text-slate-400">—</p>
                  )}
                </div>
              </div>

              <button
                onClick={refreshStatus}
                className="inline-flex items-center gap-2 text-xs font-medium text-primary hover:text-primary-hover transition px-3 py-1.5 rounded-lg hover:bg-primary/5 w-fit"
              >
                <RefreshCw size={13} /> Atualizar status
              </button>
            </div>
          )}
        </div>

        {/* Save bar — always visible so user can save from any tab */}
        <div className="flex items-center justify-center gap-3 py-2">
          <button
            onClick={handleSalvar}
            disabled={saving}
            className={`inline-flex items-center gap-2 font-semibold px-8 py-2.5 rounded-xl transition disabled:opacity-50 text-sm ${
              saved
                ? 'bg-emerald-500 text-white'
                : 'bg-primary hover:bg-primary-hover text-white'
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
