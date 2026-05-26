import { MessageSquare, FileText, Calendar, Clock } from 'lucide-react'
import SectionHeader from '../ui/SectionHeader'
import TestConnectionButton from '../TestConnectionButton'
import PasswordConfigInput from '../PasswordConfigInput'
import ListaContatosWhatsApp from '../ListaContatosWhatsApp'
import { REPORT_DAYS } from './types'
import type { TabProps } from './types'
import { testarWhatsApp } from '../../api/admin'

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

export default function ConfigWhatsApp({ form, updateField }: TabProps) {
  return (
    <div className="p-5 flex flex-col gap-8">
      {/* Twilio credentials */}
      <div>
        <div className="mb-3">
          <SectionHeader icon={MessageSquare} title="Twilio" description="Credenciais para envio via WhatsApp" />
        </div>
        <div className="ml-9 flex flex-col gap-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <PasswordConfigInput label="Account SID" value={form.twilio_account_sid ?? ''} onChange={(v) => updateField('twilio_account_sid', v)} placeholder="ACxxxxxxxxxxxxxxxx" />
            <PasswordConfigInput label="Auth Token" value={form.twilio_auth_token ?? ''} onChange={(v) => updateField('twilio_auth_token', v)} placeholder="••••••••" />
          </div>
          <PasswordConfigInput label="From Number" value={form.twilio_from_number ?? ''} onChange={(v) => updateField('twilio_from_number', v)} placeholder="whatsapp:+5511999999999" />
          <TestConnectionButton label="Testar WhatsApp" onTest={testarWhatsApp} warningText="Testa a configuração salva no servidor, não as alterações pendentes" />
        </div>
      </div>

      {/* Weekly report */}
      <div className="border-t border-border/50 pt-4">
        <div className="mb-3">
          <SectionHeader icon={FileText} title="Relatório semanal" description="Dia, horário e contatos para envio" />
        </div>
        <div className="ml-9 flex flex-col gap-3">
          <div className="flex gap-3 flex-wrap">
            <CompactSelect label="Dia" icon={Calendar} value={form.report_day ?? 'friday'} onChange={(e) => updateField('report_day', e.target.value)}>
              {REPORT_DAYS.map((d) => (<option key={d.value} value={d.value}>{d.label}</option>))}
            </CompactSelect>
            <div className="flex flex-col gap-1">
              <label className="form-label flex items-center gap-1"><Clock size={11} className="text-text-muted" />Horário</label>
              <input type="time" className="form-input-base" value={form.report_time ?? '18:00'} onChange={(e) => updateField('report_time', e.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-[11px] font-medium text-text-muted">Contatos</label>
            <ListaContatosWhatsApp />
          </div>
        </div>
      </div>
    </div>
  )
}
