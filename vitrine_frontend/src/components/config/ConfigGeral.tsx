import { useRef } from 'react'
import { MapPin, Globe, Hash, DollarSign, Target, Image as ImageIcon, Upload, Building2 } from 'lucide-react'
import SectionHeader from '../ui/SectionHeader'
import { ESTADOS_BR } from './types'
import type { TabProps } from './types'

interface ConfigGeralProps extends TabProps {
  logoPreview: string | null
  handleLogoUpload: (file: File) => Promise<void>
}

function CompactInput({
  label, icon: Icon, className, ...inputProps
}: { label: string; icon?: React.ElementType } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex flex-col gap-1">
      <label className="form-label flex items-center gap-1">
        {Icon && <Icon size={11} className="text-text-muted" />}
        {label}
      </label>
      <input className={`form-input-base${className ? ` ${className}` : ''}`} {...inputProps} />
    </div>
  )
}

function CompactSelect({
  label, icon: Icon, children, ...selectProps
}: { label: string; icon?: React.ElementType; children: React.ReactNode } & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="flex flex-col gap-1">
      <label className="form-label flex items-center gap-1">
        {Icon && <Icon size={11} className="text-text-muted" />}
        {label}
      </label>
      <select className="form-input-base" {...selectProps}>{children}</select>
    </div>
  )
}

export default function ConfigGeral({ form, updateField, logoPreview, handleLogoUpload }: ConfigGeralProps) {
  const fileRef = useRef<HTMLInputElement>(null)

  return (
    <div className="p-5 flex flex-col">
      {/* Branding */}
      <div className="mb-10">
        <div className="mb-3">
          <SectionHeader icon={Building2} title="Identidade da loja" description="Nome e logo exibidos no sistema" />
        </div>
        <div className="ml-9 flex flex-col items-start gap-3">
          <div className="relative group">
            <div className="w-24 h-24 rounded-2xl border-2 border-dashed border-border bg-bg-hover/50 flex items-center justify-center overflow-hidden">
              {logoPreview ? (
                <img src={logoPreview} alt="Logo" className="w-full h-full object-contain rounded-2xl" />
              ) : (
                <ImageIcon size={28} className="text-text-muted" />
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
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleLogoUpload(f) }}
            />
          </div>
          <div className="flex-1 w-full">
            <input
              className="w-full text-lg font-bold text-text-primary border-b-2 border-border-input bg-transparent px-1 py-1.5 focus:outline-none focus:border-primary transition placeholder:text-slate-300 dark:placeholder:text-slate-600"
              value={form.nome_estabelecimento ?? ''}
              onChange={(e) => updateField('nome_estabelecimento', e.target.value)}
              placeholder="Nome da sua loja"
            />
            <p className="text-[11px] text-text-muted mt-1 ml-1">Exibido no cabeçalho e nos relatórios</p>
          </div>
        </div>
      </div>

      {/* Address */}
      <div className="mb-10 pt-6 border-t border-border/20">
        <div className="mb-3">
          <SectionHeader icon={MapPin} title="Endereço" description="Informações de localização do estabelecimento" />
        </div>
        <div className="ml-9 flex flex-col gap-3 max-w-md">
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
            <CompactInput label="Rua / Logradouro" icon={Globe} value={form.endereco_rua ?? ''} onChange={(e) => updateField('endereco_rua', e.target.value)} placeholder="Av. Brasil" />
            <CompactInput label="Número" icon={Hash} type="text" value={form.endereco_numero ?? ''} onChange={(e) => updateField('endereco_numero', e.target.value)} placeholder="123" className="max-w-[100px]" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
            <CompactInput label="Complemento" value={form.endereco_complemento ?? ''} onChange={(e) => updateField('endereco_complemento', e.target.value)} placeholder="Sala 2, Bloco A" />
            <CompactInput label="Bairro" value={form.endereco_bairro ?? ''} onChange={(e) => updateField('endereco_bairro', e.target.value)} placeholder="Centro" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_auto] gap-3">
            <CompactInput label="Cidade" icon={MapPin} value={form.endereco_cidade ?? ''} onChange={(e) => updateField('endereco_cidade', e.target.value)} placeholder="São Paulo" />
            <CompactSelect label="UF" value={form.endereco_estado ?? ''} onChange={(e) => updateField('endereco_estado', e.target.value)}>
              <option value="">—</option>
              {ESTADOS_BR.map((uf) => (<option key={uf} value={uf}>{uf}</option>))}
            </CompactSelect>
            <CompactInput label="CEP" value={form.endereco_cep ?? ''} onChange={(e) => updateField('endereco_cep', e.target.value)} placeholder="01001-000" maxLength={9} className="max-w-[130px]" />
          </div>
        </div>
      </div>

      {/* Metas */}
      <div className="pt-6 border-t border-border/20">
        <div className="mb-3">
          <SectionHeader icon={Target} title="Metas" description="Metas de faturamento para projeção no dashboard" />
        </div>
        <div className="ml-9 flex flex-col gap-3">
          <CompactInput label="Meta de Faturamento Mensal (R$)" icon={DollarSign} type="number" value={form.meta_faturamento_mensal ?? ''} onChange={(e) => updateField('meta_faturamento_mensal', e.target.value)} placeholder="100000" className="max-w-[160px]" />
          <p className="text-[11px] text-text-muted ml-1">Usada para calcular o percentual atingido e a projeção de receita no Dashboard</p>
        </div>
      </div>
    </div>
  )
}
