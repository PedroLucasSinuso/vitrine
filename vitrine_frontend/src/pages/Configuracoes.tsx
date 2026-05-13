import { useState, useEffect, useRef } from 'react'
import AdminHeader from '../components/AdminHeader'
import ListaContatosWhatsApp from '../components/ListaContatosWhatsApp'
import ListaContatosEmail from '../components/ListaContatosEmail'
import { getConfiguracoes, atualizarConfiguracoes, uploadLogo } from '../api/admin'
import { invalidateConfigCache } from '../stores/configStore'
import { useToast } from '../hooks/useToast'

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
  { value: '0.5', label: '30 minutos' },
  { value: '1', label: '1 hora' },
  { value: '2', label: '2 horas' },
  { value: '6', label: '6 horas' },
  { value: '12', label: '12 horas' },
  { value: '24', label: '24 horas' },
]

export default function Configuracoes() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [logoPreview, setLogoPreview] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const [form, setForm] = useState({
    market_name: '',
    etl_interval_hours: '1',
    report_time: '18:00',
    report_day: 'friday',
  })

  useEffect(() => {
    getConfiguracoes()
      .then((data) => {
        const c = data.configuracoes
        setForm((prev) => ({
          market_name: c.market_name ?? prev.market_name,
          etl_interval_hours: c.etl_interval_hours ?? prev.etl_interval_hours,
          report_time: c.report_time ?? prev.report_time,
          report_day: c.report_day ?? prev.report_day,
        }))
        if (c.logo_url) setLogoPreview(c.logo_url)
        if (c.market_name) localStorage.setItem('marketName', c.market_name)
        if (c.logo_url) localStorage.setItem('marketLogoUrl', c.logo_url)
      })
      .catch(() => toast({ type: 'error', message: 'Erro ao carregar configurações' }))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps -- Mount-only fetch

  async function handleSalvar() {
    setSaving(true)
    try {
      const valores: Record<string, string> = {
        market_name: form.market_name,
        etl_interval_hours: form.etl_interval_hours,
        report_time: form.report_time,
        report_day: form.report_day,
      }
      const resp = await atualizarConfiguracoes(valores)
      const c = resp.configuracoes
      invalidateConfigCache()
      if (c.market_name) localStorage.setItem('marketName', c.market_name)
      if (c.logo_url) { localStorage.setItem('marketLogoUrl', c.logo_url); setLogoPreview(c.logo_url) }
      toast({ type: 'success', message: 'Configurações salvas' })
    } catch {
      toast({ type: 'error', message: 'Erro ao salvar configurações' })
    } finally {
      setSaving(false)
    }
  }

  async function handleLogoUpload(file: File) {
    try {
      const result = await uploadLogo(file)
      invalidateConfigCache()
      setLogoPreview(result.logo_url)
      localStorage.setItem('marketLogoUrl', result.logo_url)
      toast({ type: 'success', message: 'Logo atualizada' })
    } catch {
      toast({ type: 'error', message: 'Erro ao fazer upload da logo' })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
        <AdminHeader titulo="Configurações" paginaAtual="configuracoes" />
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-8">Carregando...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-950 flex flex-col items-center px-4 py-6">
      <AdminHeader titulo="Configurações" paginaAtual="configuracoes" />

      <div className="w-full max-w-2xl flex flex-col gap-5">

        {/* Loja */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-4">
          <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200">Loja</h2>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400">Nome da loja</label>
            <input
              className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              value={form.market_name}
              onChange={(e) => setForm((prev) => ({ ...prev, market_name: e.target.value }))}
              placeholder="Ex: Supermercado Vitória"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400">Logo</label>
            <div className="flex items-center gap-4">
              {logoPreview ? (
                <img src={logoPreview} alt="Logo" className="h-10 w-auto rounded" />
              ) : (
                <div className="w-10 h-10 rounded-lg bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-gray-400 dark:text-gray-500 text-xs">
                  Sem logo
                </div>
              )}
              <button
                onClick={() => fileRef.current?.click()}
                className="text-xs bg-primary hover:bg-primary-hover text-white font-semibold px-4 py-2 rounded-lg transition"
              >
                {logoPreview ? 'Trocar' : 'Upload'}
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

        {/* ETL */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-4">
          <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200">Sincronização ETL</h2>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400">Intervalo automático</label>
            <select
              className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary w-48"
              value={form.etl_interval_hours}
              onChange={(e) => setForm((prev) => ({ ...prev, etl_interval_hours: e.target.value }))}
            >
              {ETL_INTERVALS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Relatório WhatsApp */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-4">
          <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200">Relatório Semanal WhatsApp</h2>

          <div className="flex gap-4 flex-wrap">
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500 dark:text-gray-400">Dia da semana</label>
              <select
                className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={form.report_day}
                onChange={(e) => setForm((prev) => ({ ...prev, report_day: e.target.value }))}
              >
                {REPORT_DAYS.map((d) => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs text-gray-500 dark:text-gray-400">Horário</label>
              <input
                type="time"
                className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                value={form.report_time}
                onChange={(e) => setForm((prev) => ({ ...prev, report_time: e.target.value }))}
              />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400">Contatos</label>
            <ListaContatosWhatsApp />
          </div>
        </div>

        {/* Relatório Email */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-5 flex flex-col gap-4">
          <h2 className="text-base font-semibold text-gray-700 dark:text-gray-200">Relatório Semanal por Email</h2>

          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-500 dark:text-gray-400">Contatos</label>
            <ListaContatosEmail />
          </div>
        </div>

        {/* Salvar */}
        <button
          onClick={handleSalvar}
          disabled={saving}
          className="bg-primary hover:bg-primary-hover text-white font-semibold py-3 rounded-xl transition disabled:opacity-50 text-sm w-full max-w-xs mx-auto"
        >
          {saving ? 'Salvando...' : 'Salvar configurações'}
        </button>

      </div>
    </div>
  )
}
