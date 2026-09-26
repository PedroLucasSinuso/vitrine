import { useCallback, useEffect, useState } from 'react'
import { Copy, Target, Users } from 'lucide-react'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import ErrorBanner from '../components/ui/ErrorBanner'
import SectionHeader from '../components/ui/SectionHeader'
import {
  copiarMetas, listarAliases, listarVendedores, obterMetas, salvarAliases, salvarMetas,
} from '../api/equipe'
import { useAuth } from '../hooks/useAuth'
import { useToast } from '../hooks/useToast'
import type { MetaVendedor } from '../types'
import { competenciaAnterior, competenciaAtual, linhasDeMeta, metasParaSalvar } from '../utils/metas'

function UnificarNomes({ podeEditar }: { podeEditar: boolean }) {
  const { toast } = useToast()
  const [nomes, setNomes] = useState<string[]>([])
  const [destino, setDestino] = useState<Record<string, string>>({})
  const [salvando, setSalvando] = useState(false)

  useEffect(() => {
    Promise.all([listarVendedores(), listarAliases()])
      .then(([vendedores, aliases]) => {
        setNomes(vendedores)
        setDestino(Object.fromEntries(aliases.map((a) => [a.nome_origem, a.vendedor])))
      })
      .catch(() => setNomes([]))
  }, [])

  async function salvar() {
    setSalvando(true)
    try {
      const aliases = Object.entries(destino).filter(([, v]) => v).map(([nome_origem, vendedor]) => ({ nome_origem, vendedor }))
      await salvarAliases(aliases)
      toast({ type: 'success', message: 'Nomes unificados' })
    } finally {
      setSalvando(false)
    }
  }

  if (nomes.length < 2) return null
  return (
    <Card variant="bordered">
      <SectionHeader icon={Users}>Unificar nomes de vendedor</SectionHeader>
      <p className="text-sm text-text-secondary mt-2">
        Relatórios diferentes podem escrever o mesmo vendedor de jeitos diferentes. Indique quando um nome é outra forma de escrever alguém.
      </p>
      <div className="flex flex-col divide-y divide-border mt-3">
        {nomes.map((nome) => (
          <label key={nome} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
            <span className="text-text-primary">{nome}</span>
            <select
              className="form-input-base text-sm"
              style={{ width: '18rem', maxWidth: '100%' }}
              value={destino[nome] ?? ''}
              disabled={!podeEditar}
              onChange={(e) => setDestino({ ...destino, [nome]: e.target.value })}
            >
              <option value="">é um vendedor próprio</option>
              {nomes.filter((n) => n !== nome).map((n) => <option key={n} value={n}>é o mesmo que {n}</option>)}
            </select>
          </label>
        ))}
      </div>
      {podeEditar && <div className="mt-3"><Button variant="outline" onClick={salvar} loading={salvando}>Salvar unificação</Button></div>}
    </Card>
  )
}

export default function Metas() {
  const { getRole } = useAuth()
  const { toast } = useToast()
  const podeEditar = getRole() === 'admin'
  const [competencia, setCompetencia] = useState(competenciaAtual)
  const [linhas, setLinhas] = useState<MetaVendedor[]>([])
  const [carregando, setCarregando] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const aplicar = useCallback((dados: { metas: MetaVendedor[]; vendedores_conhecidos: string[] }) => {
    setLinhas(linhasDeMeta(
      dados.metas.map((m) => ({ ...m, valor_meta: Number(m.valor_meta), percentual_comissao: Number(m.percentual_comissao) })),
      dados.vendedores_conhecidos,
    ))
  }, [])

  const carregar = useCallback((c: string) => {
    setCarregando(true)
    setErro(null)
    obterMetas(c)
      .then(aplicar)
      .catch(() => setErro('Não foi possível carregar as metas.'))
      .finally(() => setCarregando(false))
  }, [aplicar])

  useEffect(() => { const t = setTimeout(() => carregar(competencia)); return () => clearTimeout(t) }, [carregar, competencia])

  function alterar(indice: number, campo: 'valor_meta' | 'percentual_comissao', valor: string) {
    setLinhas(linhas.map((l, i) => (i === indice ? { ...l, [campo]: Number(valor.replace(',', '.')) || 0 } : l)))
  }

  async function salvar() {
    setSalvando(true)
    try {
      aplicar(await salvarMetas(competencia, metasParaSalvar(linhas)))
      toast({ type: 'success', message: 'Metas salvas' })
    } catch {
      setErro('Não foi possível salvar. Confira os valores.')
    } finally {
      setSalvando(false)
    }
  }

  async function copiar() {
    aplicar(await copiarMetas(competencia, competenciaAnterior(competencia)))
    toast({ type: 'success', message: 'Metas copiadas do mês anterior' })
  }

  return (
    <div className="flex flex-col gap-5 max-w-full">
      <div className="page-section-header mb-0">
        <div>
          <h1 className="page-section-title">Metas da equipe</h1>
          <p className="page-section-subtitle">Meta mensal de faturamento líquido e comissão por vendedor.</p>
        </div>
      </div>
      <Card variant="bordered">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-text-muted">
            Mês
            <input type="month" className="form-input-base" value={competencia} onChange={(e) => e.target.value && setCompetencia(e.target.value)} />
          </label>
          {podeEditar && (
            <Button variant="ghost" onClick={copiar}><Copy size={14} /> Copiar do mês anterior</Button>
          )}
        </div>
        {erro && <div className="mt-3"><ErrorBanner message={erro} /></div>}
        <SectionHeader icon={Target}>Vendedores</SectionHeader>
        {carregando ? (
          <p className="text-sm text-text-muted mt-2">Carregando...</p>
        ) : linhas.length === 0 ? (
          <p className="text-sm text-text-muted mt-2">Nenhum vendedor nos dados importados ainda.</p>
        ) : (
          <table className="w-full text-sm mt-2">
            <thead>
              <tr className="text-left text-xs text-text-muted">
                <th className="py-2">Vendedor</th>
                <th className="py-2 text-right">Meta (R$)</th>
                <th className="py-2 text-right">Comissão (%)</th>
              </tr>
            </thead>
            <tbody>
              {linhas.map((l, i) => (
                <tr key={l.vendedor} className="border-t border-border">
                  <td className="py-2 text-text-primary">{l.vendedor}</td>
                  <td className="py-2 text-right">
                    <input aria-label={`Meta de ${l.vendedor}`} inputMode="decimal" className="form-input-base text-right" style={{ width: '9rem' }} disabled={!podeEditar}
                      value={l.valor_meta || ''} onChange={(e) => alterar(i, 'valor_meta', e.target.value)} />
                  </td>
                  <td className="py-2 text-right">
                    <input aria-label={`Comissão de ${l.vendedor}`} inputMode="decimal" className="form-input-base text-right" style={{ width: '6rem' }} disabled={!podeEditar}
                      value={l.percentual_comissao || ''} onChange={(e) => alterar(i, 'percentual_comissao', e.target.value)} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {podeEditar && linhas.length > 0 && (
          <div className="mt-4"><Button onClick={salvar} loading={salvando}>Salvar metas</Button></div>
        )}
      </Card>
      <UnificarNomes podeEditar={podeEditar} />
    </div>
  )
}
