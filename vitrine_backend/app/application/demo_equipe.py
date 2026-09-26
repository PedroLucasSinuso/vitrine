from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.demo import equipe
from app.application.equipe.metas import salvar_metas
from app.application.importacao.exemplo import (
    LINHA_CABECALHO_EXEMPLO,
    mapeamento_do_exemplo,
    nome_do_arquivo,
    relatorio_por_vendedor,
)
from app.application.importacao.extracao import extrair
from app.application.importacao.normalizacao import assinatura_linha
from app.application.importacao.persistencia import gravar_dataset
from app.domain.models.importacao import TemplateImportacao
from vitrine_core.bi.equipe import meses_ate
from vitrine_core.datasets.tipos import TipoDataset

MESES_DA_DEMO = 6
LOJA_DO_EXEMPLO = "VITRINE - SHOPPING CENTRAL"
COMISSAO_PADRAO = Decimal("2")
COMISSAO_DESTAQUE = Decimal("2.5")


def _periodos(hoje: date) -> list[tuple[date, date]]:
    return [(inicio, fim) for inicio, fim, _ in meses_ate(hoje, MESES_DA_DEMO)]


def _registros_de_vendas(linhas: list[equipe.LinhaMensal]) -> list[dict]:
    return [
        {
            "vendedor": linha.vendedor.upper(),
            "atendimentos": linha.atendimentos,
            "pecas": linha.pecas,
            "faturamento_bruto": linha.bruto,
            "trocas": linha.trocas,
        }
        for linha in linhas
    ]


def _registros_de_contatos(linhas: list[equipe.LinhaMensal]) -> list[dict]:
    return [
        {"vendedor": linha.vendedor.upper(), "contatos": linha.contatos, "respostas": round(linha.contatos * 0.42), "conversoes": None}
        for linha in linhas
        if linha.contatos is not None
    ]


def _semear_metas(session: Session, empresa_id: int, base: list[equipe.LinhaMensal], competencias: list[str]) -> None:
    liquido = {l.vendedor.upper(): l.bruto - l.trocas for l in base}
    destaque = max(liquido, key=liquido.get) if liquido else None
    itens = [
        {
            "vendedor": vendedor,
            "valor_meta": max(Decimal("3000"), (valor * Decimal("1.1") / 500).quantize(Decimal("1")) * 500),
            "percentual_comissao": COMISSAO_DESTAQUE if vendedor == destaque else COMISSAO_PADRAO,
        }
        for vendedor, valor in liquido.items()
    ]
    for competencia in competencias:
        salvar_metas(session, empresa_id, competencia, itens, None)


def relatorio_exemplo(hoje: date | None = None) -> tuple[str, bytes]:
    hoje = hoje or date.today()
    inicio, fim = _periodos(hoje)[-2]
    linhas = sorted(equipe.linhas_do_periodo(inicio, fim, hoje), key=lambda l: l.vendedor.upper())
    dados = [(l.vendedor.upper(), l.atendimentos, l.pecas, l.bruto, l.trocas) for l in linhas]
    return nome_do_arquivo(inicio), relatorio_por_vendedor(LOJA_DO_EXEMPLO, inicio, fim, hoje, dados)


def _registrar_template_do_exemplo(session: Session, hoje: date) -> None:
    nome, conteudo = relatorio_exemplo(hoje)
    grade = extrair(conteudo, nome)
    assinatura = assinatura_linha(grade.linhas[LINHA_CABECALHO_EXEMPLO])
    if session.scalar(select(TemplateImportacao.id).where(TemplateImportacao.assinatura == assinatura).limit(1)) is None:
        mapeamento = mapeamento_do_exemplo()
        session.add(TemplateImportacao(
            assinatura=assinatura, versao=1, tipo=mapeamento.tipo.value,
            mapeamento=mapeamento.sem_posicao(), erp_origem="exemplo", usos=0,
        ))


def popular_equipe(session: Session, empresa_id: int, hoje: date | None = None) -> None:
    hoje = hoje or date.today()
    periodos = _periodos(hoje)
    por_periodo = {p: equipe.linhas_do_periodo(*p, hoje) for p in periodos}
    for (inicio, fim), linhas in por_periodo.items():
        sufixo = f"{inicio:%Y-%m}"
        gravar_dataset(
            session, empresa_id, TipoDataset.VENDAS_VENDEDOR_PERIODO, (inicio, fim),
            _registros_de_vendas(linhas), nome_origem=f"vendas-por-vendedor-{sufixo}.xlsx",
        )
        contatos = _registros_de_contatos(linhas)
        if contatos:
            gravar_dataset(
                session, empresa_id, TipoDataset.CONTATOS_VENDEDOR, (inicio, fim),
                contatos, nome_origem=f"contatos-dito-{sufixo}.csv",
            )
    session.flush()
    passado, corrente = periodos[-2], periodos[-1]
    _semear_metas(
        session, empresa_id, por_periodo[passado],
        [f"{passado[0]:%Y-%m}", f"{corrente[0]:%Y-%m}"],
    )
    _registrar_template_do_exemplo(session, hoje)
