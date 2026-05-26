import { Mail, Globe, Hash, Send, FileText, Calendar, Clock } from 'lucide-react'
import SectionHeader from '../ui/SectionHeader'
import TestConnectionButton from '../TestConnectionButton'
import PasswordConfigInput from '../PasswordConfigInput'
import ListaContatosEmail from '../ListaContatosEmail'
import { REPORT_DAYS } from './types'
import type { TabProps } from './types'
import { testarEmail } from '../../api/admin'

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

export default function ConfigEmail({ form, updateField }: TabProps) {
  return (
    <div className="p-5 flex flex-col gap-8">
      {/* SMTP */}
      <div>
        <div className="mb-3">
          <SectionHeader icon={Mail} title="SMTP" description="Servidor de e-mail para envio de relatórios" />
        </div>
        <div className="ml-9 flex flex-col gap-3">
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
            <CompactInput label="Host" icon={Globe} value={form.smtp_host ?? ''} onChange={(e) => updateField('smtp_host', e.target.value)} placeholder="smtp.gmail.com" />
            <CompactInput label="Porta" icon={Hash} type="number" min="1" value={form.smtp_port ?? '587'} onChange={(e) => updateField('smtp_port', e.target.value)} className="max-w-[90px]" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <CompactInput label="Usuário" value={form.smtp_user ?? ''} onChange={(e) => updateField('smtp_user', e.target.value)} placeholder="email@dominio.com" />
            <PasswordConfigInput label="Senha" value={form.smtp_password ?? ''} onChange={(v) => updateField('smtp_password', v)} placeholder="••••••••" />
          </div>
          <CompactInput label="E-mail remetente" icon={Send} value={form.email_from ?? ''} onChange={(e) => updateField('email_from', e.target.value)} placeholder="relatorios@dominio.com" />
          <TestConnectionButton label="Testar E-mail" onTest={testarEmail} warningText="Testa a configuração salva no servidor, não as alterações pendentes" />
        </div>
      </div>

      {/* Weekly report */}
      <div className="border-t border-border/50 pt-4">
        <div className="mb-3">
          <SectionHeader icon={FileText} title="Relatório semanal" description="Dia, horário e contatos para envio" />
        </div>
        <div className="ml-9 flex flex-col gap-3">
          <div className="flex gap-3 flex-wrap">
            <CompactSelect label="Dia" icon={Calendar} value={form.report_email_day ?? 'friday'} onChange={(e) => updateField('report_email_day', e.target.value)}>
              {REPORT_DAYS.map((d) => (<option key={d.value} value={d.value}>{d.label}</option>))}
            </CompactSelect>
            <div className="flex flex-col gap-1">
              <label className="form-label flex items-center gap-1"><Clock size={11} className="text-text-muted" />Horário</label>
              <input type="time" className="form-input-base" value={form.report_email_time ?? '18:00'} onChange={(e) => updateField('report_email_time', e.target.value)} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-[11px] font-medium text-text-muted">Contatos</label>
            <ListaContatosEmail />
          </div>
        </div>
      </div>
    </div>
  )
}
