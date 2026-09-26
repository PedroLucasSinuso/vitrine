import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { AlertTriangle, CheckCircle2, FileSpreadsheet, History, Sparkles, Upload, XCircle } from 'lucide-react'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import ErrorBanner from '../components/ui/ErrorBanner'
import SectionHeader from '../components/ui/SectionHeader'
import {
  confirmarImportacao, enviarArquivo, listarCampos, listarImportacoes, obterImportacao, salvarMapeamento,
} from '../api/importacao'
import { useToast } from '../hooks/useToast'
import type { CampoDataset, Celula, Importacao, ImportacaoResumo, Mapeamento, TipoDataset } from '../types'
import { NOMES_TIPO_DATASET, formatarDataCurta } from '../utils/equipe'
import { TIPOS_POR_PERIODO, largura, linhaDeCabecalhoProvavel, sugerirColunas, sugerirTipo } from '../utils/importacao'

const ROTULO_STATUS: Record<string, string> = {
  aguardando_mapeamento: 'Aguardando mapeamento',
  pronto: 'Pronto para confirmar',
  divergente: 'Totais não conferem',
  confirmado: 'Confirmado',
  erro: 'Erro',
}

function mensagemDeErro(e: unknown, padrao: string): string {
  const detalhe = (e as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
  if (typeof detalhe === 'string') return detalhe
  if (Array.isArray(detalhe)) return detalhe.map((d: { msg?: string }) => d.msg ?? '').join(' ')
  return padrao
}

function mapeamentoInicial(importacao: Importacao, campos: Record<TipoDataset, CampoDataset[]> | null): Mapeamento {
  if (importacao.mapeamento) return importacao.mapeamento
  const linha = linhaDeCabecalhoProvavel(importacao.grade)
  const tipo = sugerirTipo(importacao.grade[linha] ?? [])
  return {
    tipo,
    linha_cabecalho: linha,
    colunas: campos ? sugerirColunas(importacao.grade[linha] ?? [], campos[tipo]) : [],
    formato_data: 'dd/mm/aaaa',
    separador_decimal: ',',
    periodo: null,
  }
}

const ROTULO_CONFIANCA = { alta: 'alta', media: 'média', baixa: 'baixa' } as const

function SugestaoAutomatica({ sugestao }: { sugestao: NonNullable<Importacao['sugestao_ia']> }) {
  if (sugestao.erro) {
    return (
      <p className="text-sm text-text-muted flex items-center gap-2">
        <AlertTriangle size={16} /> Sugestão automática indisponível: {sugestao.erro} Mapeie as colunas abaixo.
      </p>
    )
  }
  return (
    <div className="rounded-lg border border-border bg-bg-card px-4 py-3 text-sm">
      <p className="flex items-center gap-2 text-text-primary">
        <Sparkles size={16} className="text-primary" />
        Mapeamento sugerido automaticamente
        {sugestao.confianca && <span className="text-text-muted">(confiança {ROTULO_CONFIANCA[sugestao.confianca]})</span>}
        — confira a prévia antes de confirmar.
      </p>
      {sugestao.duvidas.length > 0 && (
        <ul className="mt-2 ml-6 list-disc text-text-secondary">
          {sugestao.duvidas.map((d) => <li key={d}>{d}</li>)}
        </ul>
      )}
    </div>
  )
}

function Celulas({ linha, colunas }: { linha: Celula[]; colunas: number }) {
  return (
    <>
      {Array.from({ length: colunas }).map((_, i) => (
        <td key={i} className="px-2 py-1 border-b border-border whitespace-nowrap max-w-[220px] truncate">
          {linha[i] ?? ''}
        </td>
      ))}
    </>
  )
}

function EditorDeMapeamento({
  importacao, campos, onSalvo,
}: {
  importacao: Importacao
  campos: Record<TipoDataset, CampoDataset[]>
  onSalvo: (i: Importacao) => void
}) {
  const [mapeamento, setMapeamento] = useState<Mapeamento>(() => mapeamentoInicial(importacao, campos))
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const colunas = largura(importacao.grade)
  const camposDoTipo = campos[mapeamento.tipo]
  const porPeriodo = TIPOS_POR_PERIODO.includes(mapeamento.tipo)

  function campoDaColuna(indice: number): string {
    return mapeamento.colunas.find((c) => c.indice === indice)?.campo ?? ''
  }

  function definirCampo(indice: number, campo: string) {
    const outras = mapeamento.colunas.filter((c) => c.indice !== indice && c.campo !== campo)
    setMapeamento({ ...mapeamento, colunas: campo ? [...outras, { indice, campo }] : outras })
  }

  function definirTipo(tipo: TipoDataset) {
    const cabecalho = importacao.grade[mapeamento.linha_cabecalho] ?? []
    setMapeamento({ ...mapeamento, tipo, colunas: sugerirColunas(cabecalho, campos[tipo]) })
  }

  function definirCabecalho(linha: number) {
    setMapeamento({ ...mapeamento, linha_cabecalho: linha, colunas: sugerirColunas(importacao.grade[linha] ?? [], camposDoTipo) })
  }

  async function salvar() {
    setErro(null)
    setSalvando(true)
    try {
      onSalvo(await salvarMapeamento(importacao.id, { ...mapeamento, periodo: porPeriodo ? mapeamento.periodo : null }))
    } catch (e) {
      setErro(mensagemDeErro(e, 'Não foi possível aplicar o mapeamento.'))
    } finally {
      setSalvando(false)
    }
  }

  const faltando = camposDoTipo.filter((c) => c.obrigatorio && !mapeamento.colunas.some((m) => m.campo === c.campo))

  return (
    <Card variant="bordered">
      <SectionHeader icon={FileSpreadsheet}>Como ler este relatório</SectionHeader>
      <div className="flex flex-wrap gap-4 mt-3">
        <label className="flex flex-col gap-1 text-xs text-text-muted">
          O relatório traz
          <select className="form-input-base" value={mapeamento.tipo} onChange={(e) => definirTipo(e.target.value as TipoDataset)}>
            {(Object.keys(NOMES_TIPO_DATASET) as TipoDataset[]).map((t) => <option key={t} value={t}>{NOMES_TIPO_DATASET[t]}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-text-muted">
          Números
          <select className="form-input-base" value={mapeamento.separador_decimal} onChange={(e) => setMapeamento({ ...mapeamento, separador_decimal: e.target.value as ',' | '.' })}>
            <option value=",">1.234,56</option>
            <option value=".">1,234.56</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-text-muted">
          Datas
          <select className="form-input-base" value={mapeamento.formato_data} onChange={(e) => setMapeamento({ ...mapeamento, formato_data: e.target.value as Mapeamento['formato_data'] })}>
            <option value="dd/mm/aaaa">dd/mm/aaaa</option>
            <option value="aaaa-mm-dd">aaaa-mm-dd</option>
            <option value="mm/dd/aaaa">mm/dd/aaaa</option>
          </select>
        </label>
        {porPeriodo && (
          <>
            <label className="flex flex-col gap-1 text-xs text-text-muted">
              Período — início
              <input type="date" className="form-input-base" value={mapeamento.periodo?.inicio ?? ''}
                onChange={(e) => setMapeamento({ ...mapeamento, periodo: e.target.value ? { inicio: e.target.value, fim: mapeamento.periodo?.fim ?? e.target.value } : null })} />
            </label>
            <label className="flex flex-col gap-1 text-xs text-text-muted">
              Período — fim
              <input type="date" className="form-input-base" value={mapeamento.periodo?.fim ?? ''}
                onChange={(e) => setMapeamento({ ...mapeamento, periodo: e.target.value ? { inicio: mapeamento.periodo?.inicio ?? e.target.value, fim: e.target.value } : null })} />
            </label>
          </>
        )}
      </div>
      {porPeriodo && !mapeamento.periodo && (
        <p className="text-xs text-text-muted mt-2">Sem período informado, o Vitrine procura as datas no topo do relatório.</p>
      )}

      <p className="text-sm text-text-secondary mt-4">
        Clique na linha que tem os nomes das colunas e escolha o que cada coluna significa.
      </p>
      <div className="overflow-x-auto mt-2 border border-border rounded-lg max-h-[420px]">
        <table className="text-xs w-full">
          <thead className="sticky top-0 bg-bg-card z-10">
            <tr>
              <th className="px-2 py-1 text-text-muted">#</th>
              {Array.from({ length: colunas }).map((_, i) => (
                <th key={i} className="px-1 py-1">
                  <select aria-label={`Campo da coluna ${i + 1}`} className="form-input-base text-xs min-w-[130px]" value={campoDaColuna(i)} onChange={(e) => definirCampo(i, e.target.value)}>
                    <option value="">— ignorar —</option>
                    {camposDoTipo.map((c) => <option key={c.campo} value={c.campo}>{c.rotulo}{c.obrigatorio ? ' *' : ''}</option>)}
                  </select>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {importacao.grade.map((linha, i) => {
              const cabecalho = i === mapeamento.linha_cabecalho
              const antes = i < mapeamento.linha_cabecalho
              return (
                <tr
                  key={i}
                  onClick={() => definirCabecalho(i)}
                  className={`cursor-pointer ${cabecalho ? 'bg-primary-light font-semibold text-text-primary' : antes ? 'text-text-muted opacity-60' : 'text-text-secondary hover:bg-bg-hover'}`}
                >
                  <td className="px-2 py-1 border-b border-border text-text-muted">{i + 1}</td>
                  <Celulas linha={linha} colunas={colunas} />
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {importacao.total_linhas > importacao.grade.length && (
        <p className="text-xs text-text-muted mt-1">Mostrando {importacao.grade.length} de {importacao.total_linhas} linhas.</p>
      )}

      {faltando.length > 0 && (
        <p className="text-xs text-warning mt-3">Faltam: {faltando.map((c) => c.rotulo).join(', ')}</p>
      )}
      {erro && <div className="mt-3"><ErrorBanner message={erro} /></div>}
      <div className="mt-4">
        <Button onClick={salvar} loading={salvando} disabled={faltando.length > 0}>Aplicar mapeamento</Button>
      </div>
    </Card>
  )
}

function formatarValor(valor: Celula, campo: CampoDataset | undefined): string {
  if (valor === null || valor === undefined) return ''
  if (campo?.tipo === 'data' && typeof valor === 'string') return formatarDataCurta(valor)
  if ((campo?.tipo === 'numero' || campo?.tipo === 'inteiro') && typeof valor === 'number') {
    return valor.toLocaleString('pt-BR', { maximumFractionDigits: 3 })
  }
  if (campo?.tipo === 'operacao') return valor === 'troca' ? 'Troca' : 'Venda'
  return String(valor)
}

function PreviaDaImportacao({
  importacao, definicoes, onConfirmar, confirmando,
}: { importacao: Importacao; definicoes: CampoDataset[]; onConfirmar: () => void; confirmando: boolean }) {
  const previa = importacao.previa
  if (!previa) return null
  const campos = [...(importacao.mapeamento?.colunas ?? [])].sort((a, b) => a.indice - b.indice).map((c) => c.campo)
  const definicao = (campo: string) => definicoes.find((d) => d.campo === campo)
  const status = previa.validacao.status
  return (
    <Card variant="bordered">
      <SectionHeader icon={CheckCircle2}>Prévia</SectionHeader>
      <div className="flex flex-col gap-3 mt-3">
        {status === 'conferido' && (
          <p className="text-sm text-success flex items-center gap-2"><CheckCircle2 size={16} /> Totais conferem com a linha de total do relatório.</p>
        )}
        {status === 'divergente' && (
          <div className="text-sm text-danger">
            <p className="flex items-center gap-2"><XCircle size={16} /> Os totais não batem com o relatório. Revise o mapeamento.</p>
            <ul className="ml-6 list-disc text-xs mt-1">
              {previa.validacao.diferencas.map((d) => (
                <li key={d.campo}>{d.campo}: calculado {d.calculado.toLocaleString('pt-BR')} × relatório {d.informado.toLocaleString('pt-BR')}</li>
              ))}
            </ul>
          </div>
        )}
        {status === 'sem_total' && (
          <p className="text-sm text-warning flex items-center gap-2"><AlertTriangle size={16} /> O relatório não tem linha de total: confira os números abaixo antes de confirmar.</p>
        )}
        {previa.erros.map((e) => <ErrorBanner key={e} message={e} />)}
        <p className="text-xs text-text-muted">
          {previa.total_registros} linhas lidas
          {previa.periodo && ` · período ${formatarDataCurta(previa.periodo.inicio)} a ${formatarDataCurta(previa.periodo.fim)}`}
          {previa.total_descartadas > 0 && ` · ${previa.total_descartadas} linhas ignoradas (títulos, subtotais, rodapé)`}
        </p>
        {previa.registros.length > 0 && (
          <div className="overflow-x-auto border border-border rounded-lg">
            <table className="text-xs w-full">
              <thead><tr>{campos.map((c) => <th key={c} className="px-2 py-1 text-left text-text-muted border-b border-border">{definicao(c)?.rotulo ?? c}</th>)}</tr></thead>
              <tbody>
                {previa.registros.map((r, i) => (
                  <tr key={i}>{campos.map((c) => <td key={c} className="px-2 py-1 border-b border-border text-text-secondary whitespace-nowrap">{formatarValor(r[c], definicao(c))}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {importacao.status !== 'confirmado' && (
          <div>
            <Button onClick={onConfirmar} loading={confirmando} disabled={!previa.confirmavel}>Confirmar importação</Button>
          </div>
        )}
      </div>
    </Card>
  )
}

export default function Importar() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const { toast } = useToast()
  const [campos, setCampos] = useState<Record<TipoDataset, CampoDataset[]> | null>(null)
  const [importacao, setImportacao] = useState<Importacao | null>(null)
  const [historico, setHistorico] = useState<ImportacaoResumo[]>([])
  const [enviando, setEnviando] = useState(false)
  const [confirmando, setConfirmando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [arrastando, setArrastando] = useState(false)
  const idAberto = params.get('id')

  const atualizarHistorico = useCallback(() => { listarImportacoes().then(setHistorico).catch(() => setHistorico([])) }, [])

  useEffect(() => {
    listarCampos().then(setCampos).catch(() => setErro('Não foi possível carregar os campos.'))
    atualizarHistorico()
  }, [atualizarHistorico])

  useEffect(() => {
    if (!idAberto || importacao?.id === Number(idAberto)) return
    obterImportacao(Number(idAberto)).then(setImportacao).catch((e) => setErro(mensagemDeErro(e, 'Importação não encontrada.')))
  }, [idAberto, importacao?.id])

  function abrir(i: Importacao) {
    setImportacao(i)
    setParams({ id: String(i.id) }, { replace: true })
  }

  async function enviar(arquivo: File | undefined) {
    if (!arquivo) return
    setErro(null)
    setEnviando(true)
    try {
      abrir(await enviarArquivo(arquivo))
      atualizarHistorico()
    } catch (e) {
      setErro(mensagemDeErro(e, 'Não foi possível ler o arquivo.'))
    } finally {
      setEnviando(false)
    }
  }

  async function confirmar() {
    if (!importacao) return
    setConfirmando(true)
    try {
      const dataset = await confirmarImportacao(importacao.id)
      toast({ type: 'success', message: `${dataset.linhas} linhas importadas` })
      abrir(await obterImportacao(importacao.id))
      atualizarHistorico()
    } catch (e) {
      setErro(mensagemDeErro(e, 'Não foi possível confirmar.'))
    } finally {
      setConfirmando(false)
    }
  }

  const chaveEditor = useMemo(() => `${importacao?.id}-${importacao?.status}-${importacao?.template_aplicado}`, [importacao])

  return (
    <div className="flex flex-col gap-5 max-w-full">
      <div className="page-section-header mb-0">
        <div>
          <h1 className="page-section-title">Importar relatório</h1>
          <p className="page-section-subtitle">Envie o relatório exportado do seu sistema (xls, xlsx, csv ou pdf).</p>
        </div>
      </div>

      <Card variant="bordered">
        <label
          onDragOver={(e) => { e.preventDefault(); setArrastando(true) }}
          onDragLeave={() => setArrastando(false)}
          onDrop={(e) => { e.preventDefault(); setArrastando(false); enviar(e.dataTransfer.files[0]) }}
          className={`flex flex-col items-center justify-center gap-2 border-2 border-dashed rounded-xl p-8 cursor-pointer transition ${arrastando ? 'border-primary bg-primary-light' : 'border-border hover:border-primary'}`}
        >
          <Upload size={28} className="text-text-muted" />
          <span className="text-sm text-text-primary font-medium">{enviando ? 'Lendo arquivo...' : 'Arraste o arquivo aqui ou clique para escolher'}</span>
          <span className="text-xs text-text-muted">Até 10 MB</span>
          <input type="file" accept=".xls,.xlsx,.csv,.txt,.pdf" className="sr-only" disabled={enviando} onChange={(e) => enviar(e.target.files?.[0])} />
        </label>
        {erro && <div className="mt-3"><ErrorBanner message={erro} /></div>}
      </Card>

      {importacao && (
        <>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="font-semibold text-text-primary">{importacao.nome}</span>
            <span className="text-text-muted">{ROTULO_STATUS[importacao.status]}</span>
            {importacao.template_aplicado && importacao.status !== 'confirmado' && (
              <span className="text-xs text-success">Layout reconhecido: mapeamento aplicado automaticamente</span>
            )}
            {importacao.duplicado_de && (
              <span className="text-xs text-warning">Este mesmo arquivo já foi importado antes</span>
            )}
          </div>
          {importacao.status !== 'confirmado' && importacao.sugestao_ia && (
            <SugestaoAutomatica sugestao={importacao.sugestao_ia} />
          )}
          {importacao.status === 'confirmado' ? (
            <Card variant="bordered">
              <p className="text-sm text-success flex items-center gap-2"><CheckCircle2 size={16} /> Importação confirmada.</p>
              <div className="flex gap-2 mt-3">
                <Button variant="outline" onClick={() => navigate('/bi/equipe')}>Ver equipe</Button>
                <Button variant="ghost" onClick={() => navigate('/datasets')}>Dados importados</Button>
              </div>
            </Card>
          ) : campos ? (
            <EditorDeMapeamento key={chaveEditor} importacao={importacao} campos={campos} onSalvo={(i) => { abrir(i); atualizarHistorico() }} />
          ) : null}
          <PreviaDaImportacao
            importacao={importacao}
            definicoes={campos && importacao.mapeamento ? campos[importacao.mapeamento.tipo] : []}
            onConfirmar={confirmar}
            confirmando={confirmando}
          />
        </>
      )}

      {historico.length > 0 && (
        <Card variant="bordered">
          <SectionHeader icon={History}>Importações recentes</SectionHeader>
          <ul className="flex flex-col divide-y divide-border mt-2">
            {historico.map((h) => (
              <li key={h.id}>
                <button className="w-full flex justify-between py-2 text-sm hover:text-primary" onClick={() => obterImportacao(h.id).then(abrir).catch((e) => setErro(mensagemDeErro(e, 'Arquivo indisponível.')))}>
                  <span className="text-text-primary">{h.nome}</span>
                  <span className="text-text-muted text-xs">{ROTULO_STATUS[h.status]} · {formatarDataCurta(h.criado_em)}</span>
                </button>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
