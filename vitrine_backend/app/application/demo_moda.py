import io
import random
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.demo import moda
from app.adapters.demo.rng import semente
from app.application.equipe.metas import salvar_metas
from app.application.importacao.extracao import extrair
from app.application.importacao.mapeamento import ColunaMapeada, Mapeamento
from app.application.importacao.normalizacao import assinatura_linha
from app.application.importacao.persistencia import gravar_dataset
from app.domain.models.importacao import TemplateImportacao
from vitrine_core.datasets.tipos import Operacao, TipoDataset

LINHA_CABECALHO_EXEMPLO = 5
COMISSAO_PADRAO = Decimal("2")
COMISSAO_DESTAQUE = Decimal("2.5")
NOMES_DOS_MESES = ("janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
                   "agosto", "setembro", "outubro", "novembro", "dezembro")


def _liquido_por_vendedor(itens: list[dict]) -> dict[str, Decimal]:
    liquido: dict[str, Decimal] = defaultdict(Decimal)
    for item in itens:
        if item["vendedor"]:
            sinal = -1 if item["operacao"] == Operacao.TROCA else 1
            liquido[item["vendedor"]] += sinal * item["valor"]
    return liquido


def _contatos(itens: list[dict], inicio: date) -> list[dict]:
    rng = random.Random(semente("moda", "contatos", inicio.isoformat()))
    atendimentos: dict[str, set] = defaultdict(set)
    for item in itens:
        if item["vendedor"] and item["operacao"] == Operacao.VENDA:
            atendimentos[item["vendedor"]].add(item["documento"])
    return [
        {
            "vendedor": vendedor,
            "contatos": round(len(documentos) * rng.uniform(1.6, 3.4)),
            "respostas": round(len(documentos) * rng.uniform(0.6, 1.2)),
            "conversoes": None,
        }
        for vendedor, documentos in sorted(atendimentos.items())
    ]


def _competencia(dia: date) -> str:
    return f"{dia.year:04d}-{dia.month:02d}"


def _semear_metas(session: Session, empresa_id: int, base: dict[str, Decimal], competencias: list[str]) -> None:
    destaque = max(base, key=base.get) if base else None
    itens = [
        {
            "vendedor": vendedor,
            "valor_meta": max(Decimal("3000"), (liquido * Decimal("1.1") / 500).quantize(Decimal("1")) * 500),
            "percentual_comissao": COMISSAO_DESTAQUE if vendedor == destaque else COMISSAO_PADRAO,
        }
        for vendedor, liquido in base.items()
    ]
    for competencia in competencias:
        salvar_metas(session, empresa_id, competencia, itens, None)


def mapeamento_do_exemplo() -> Mapeamento:
    return Mapeamento(
        tipo=TipoDataset.VENDAS_VENDEDOR_PERIODO,
        linha_cabecalho=LINHA_CABECALHO_EXEMPLO,
        colunas=[
            ColunaMapeada(indice=0, campo="vendedor"),
            ColunaMapeada(indice=1, campo="atendimentos"),
            ColunaMapeada(indice=2, campo="pecas"),
            ColunaMapeada(indice=3, campo="faturamento_bruto"),
            ColunaMapeada(indice=4, campo="trocas"),
        ],
    )


def _formatar(valor: Decimal) -> str:
    inteiro, centavos = f"{valor:.2f}".split(".")
    return f"{int(inteiro):,}".replace(",", ".") + "," + centavos


def relatorio_exemplo(hoje: date | None = None) -> tuple[str, bytes]:
    from openpyxl import Workbook

    hoje = hoje or date.today()
    inicio, fim = moda.meses_da_demo(hoje)[-2]
    itens = moda.itens_do_periodo(inicio, fim, hoje)
    por_vendedor: dict[str, dict] = defaultdict(lambda: {"docs": set(), "pecas": Decimal(0), "valor": Decimal(0), "trocas": Decimal(0)})
    for item in itens:
        if not item["vendedor"]:
            continue
        linha = por_vendedor[item["vendedor"].upper()]
        if item["operacao"] == Operacao.TROCA:
            linha["trocas"] += item["valor"]
        else:
            linha["docs"].add(item["documento"])
            linha["pecas"] += item["quantidade"]
            linha["valor"] += item["valor"]

    livro = Workbook()
    planilha = livro.active
    planilha.title = "Relatorio"
    planilha.append(["RELATÓRIO DE VENDAS POR VENDEDOR"])
    planilha.append(["Loja: VITRINE MODA - SHOPPING CENTRAL"])
    planilha.append([f"Período: {inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"])
    planilha.append([])
    planilha.append([None, "Vendas", None, None, None])
    planilha.append(["Vendedor", "Qtd Tickets", "Qtd Peças", "Valor (R$)", "Trocas (R$)"])
    planilha.merge_cells(start_row=5, start_column=2, end_row=5, end_column=4)
    total = {"docs": 0, "pecas": Decimal(0), "valor": Decimal(0), "trocas": Decimal(0)}
    for nome in sorted(por_vendedor):
        v = por_vendedor[nome]
        planilha.append([nome, len(v["docs"]), int(v["pecas"]), f"R$ {_formatar(v['valor'])}", _formatar(v["trocas"])])
        total["docs"] += len(v["docs"])
        total["pecas"] += v["pecas"]
        total["valor"] += v["valor"]
        total["trocas"] += v["trocas"]
    planilha.append(["TOTAL GERAL", total["docs"], int(total["pecas"]), _formatar(total["valor"]), _formatar(total["trocas"])])
    planilha.append([])
    planilha.append([f"Emitido em {hoje:%d/%m/%Y} por gerente.loja"])
    saida = io.BytesIO()
    livro.save(saida)
    return f"vendas-por-vendedor-{NOMES_DOS_MESES[inicio.month - 1]}.xlsx", saida.getvalue()


def registrar_template_do_exemplo(session: Session) -> None:
    _, conteudo = relatorio_exemplo()
    grade = extrair(conteudo, "exemplo.xlsx")
    assinatura = assinatura_linha(grade.linhas[LINHA_CABECALHO_EXEMPLO])
    existe = session.scalar(select(TemplateImportacao.id).where(TemplateImportacao.assinatura == assinatura).limit(1))
    if existe is None:
        mapeamento = mapeamento_do_exemplo()
        session.add(TemplateImportacao(
            assinatura=assinatura, versao=1, tipo=mapeamento.tipo.value,
            mapeamento=mapeamento.sem_posicao(), erp_origem="exemplo", usos=0,
        ))


def popular_moda(session: Session, empresa_id: int, hoje: date | None = None) -> None:
    hoje = hoje or date.today()
    meses = moda.meses_da_demo(hoje)
    liquido_mes_passado: dict[str, Decimal] = {}
    for inicio, fim in meses:
        itens = moda.itens_do_periodo(inicio, fim, hoje)
        gravar_dataset(
            session, empresa_id, TipoDataset.ITENS_VENDA, (inicio, fim), itens,
            nome_origem=f"vendas-itens-{NOMES_DOS_MESES[inicio.month - 1]}.xlsx",
        )
        gravar_dataset(
            session, empresa_id, TipoDataset.CONTATOS_VENDEDOR, (inicio, fim), _contatos(itens, inicio),
            nome_origem=f"contatos-dito-{NOMES_DOS_MESES[inicio.month - 1]}.csv",
        )
        if (inicio, fim) == meses[-2]:
            liquido_mes_passado = _liquido_por_vendedor(itens)
    session.flush()
    _semear_metas(session, empresa_id, liquido_mes_passado, [_competencia(meses[-2][0]), _competencia(meses[-1][0])])
    registrar_template_do_exemplo(session)
