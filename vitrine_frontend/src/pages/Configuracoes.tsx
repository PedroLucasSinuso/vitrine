import { useState, useEffect } from 'react'
import { Check, Loader2, Store, Database, MessageSquare, Mail, Brain } from 'lucide-react'
import Card from '../components/ui/Card'
import PageContainer from '../components/layout/PageContainer'
import ConfigGeral from '../components/config/ConfigGeral'
import ConfigErp from '../components/config/ConfigErp'
import ConfigWhatsApp from '../components/config/ConfigWhatsApp'
import ConfigEmail from '../components/config/ConfigEmail'
import ConfigIntelligence from '../components/config/ConfigIntelligence'
import { getConfiguracoes, atualizarConfiguracoes, uploadLogo } from '../api/admin'
import { invalidateConfigCache } from '../stores/configStore'
import { useToast } from '../hooks/useToast'
import type { ConfigForm } from '../components/config/types'

const TABS = [
  { id: 'geral', label: 'Geral', icon: Store },
  { id: 'erp', label: 'ERP / Sync', icon: Database },
  { id: 'whatsapp', label: 'WhatsApp', icon: MessageSquare },
  { id: 'email', label: 'E-mail', icon: Mail },
  { id: 'intelligence', label: 'Intelligence', icon: Brain },
]

export default function Configuracoes() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [activeTab, setActiveTab] = useState('geral')
  const [form, setForm] = useState<ConfigForm>({})
  const [logoPreview, setLogoPreview] = useState<string | null>(null)

  useEffect(() => {
    getConfiguracoes()
      .then((c) => {
        setForm(c.configuracoes)
        if (c.configuracoes.logo_url) setLogoPreview(c.configuracoes.logo_url)
      })
      .catch(() => toast({ type: 'error', message: 'Erro ao carregar configurações' }))
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSalvar() {
    setSaving(true)
    setSaved(false)
    try {
      const resp = await atualizarConfiguracoes(form as Record<string, string>)
      invalidateConfigCache()
      if (resp.configuracoes.logo_url) setLogoPreview(resp.configuracoes.logo_url)
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
      setForm((prev) => ({ ...prev, logo_url: result.logo_url }))
      toast({ type: 'success', message: 'Logo atualizada' })
    } catch {
      toast({ type: 'error', message: 'Erro ao fazer upload da logo' })
    }
  }

  function updateField(key: string, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  if (loading) {
    return (
      <PageContainer maxWidth="xl">
        <div className="flex items-center justify-center gap-2 text-sm text-text-muted mt-12">
          <Loader2 size={16} className="animate-spin" /> Carregando...
        </div>
      </PageContainer>
    )
  }

  return (
    <PageContainer maxWidth="xl">
      <div className="flex flex-col gap-4">
        {/* Tab bar */}
        <Card variant="default" className="p-1">
          <div className="flex gap-0.5 overflow-x-auto lg:justify-evenly">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition whitespace-nowrap shrink-0 lg:flex-1 lg:justify-center ${
                  activeTab === id
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-text-muted hover:bg-bg-hover hover:text-text-primary'
                }`}
              >
                <Icon size={13} />
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>
        </Card>

        {/* Tab content + save bar inside card */}
        <Card variant="default" padding="none">
          <div className="max-w-2xl mx-auto">
            {activeTab === 'geral' && (
              <ConfigGeral form={form} updateField={updateField} logoPreview={logoPreview} handleLogoUpload={handleLogoUpload} />
            )}
            {activeTab === 'erp' && <ConfigErp form={form} updateField={updateField} />}
            {activeTab === 'whatsapp' && <ConfigWhatsApp form={form} updateField={updateField} />}
            {activeTab === 'email' && <ConfigEmail form={form} updateField={updateField} />}
            {activeTab === 'intelligence' && <ConfigIntelligence form={form} updateField={updateField} />}

            {/* Save bar inside card, right-aligned */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border">
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
        </Card>
      </div>
    </PageContainer>
  )
}
