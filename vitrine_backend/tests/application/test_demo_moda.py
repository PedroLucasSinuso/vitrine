from datetime import date

import pytest
from sqlalchemy import func, select

from app.adapters.arquivo.transaction_source import DatasetTransactionSource
from app.application.demo_moda import mapeamento_do_exemplo, popular_moda, relatorio_exemplo
from app.application.equipe.fonte import FonteEquipeDatasets
from app.application.equipe.metas import metas_para_calculo
from app.application.equipe.servico import resultado_equipe
from app.application.importacao.aplicacao import aplicar
from app.application.importacao.extracao import extrair
from app.domain.models.importacao import Dataset, TemplateImportacao
from app.domain.models.metas import MetaVendedor
from tests.bancos import BANCOS, sessao_em_banco_limpo
from vitrine_core.bi.domain.trocas import Trocas
from vitrine_core.bi.domain.vendas import Vendas
from vitrine_core.bi.reporting.relatorio import Relatorio

HOJE = date(2026, 9, 26)
LOJA = 1
AGOSTO = (date(2026, 8, 1), date(2026, 8, 31))


@pytest.fixture(params=BANCOS)
def db(request):
    for sessao in sessao_em_banco_limpo(request.param, {LOJA: "demo-moda"}):
        popular_moda(sessao, LOJA, hoje=HOJE)
        sessao.commit()
        yield sessao


def test_seis_meses_de_itens_metas_e_template(db):
    datasets = db.scalars(select(Dataset).order_by(Dataset.inicio)).all()

    assert [(d.inicio, d.fim) for d in datasets][0] == (date(2026, 4, 1), date(2026, 4, 30))
    assert datasets[-1].fim == HOJE
    assert len(datasets) == 6
    assert {d.tipo for d in datasets} == {"itens_venda"}
    assert set(db.scalars(select(MetaVendedor.competencia).distinct())) == {"2026-08", "2026-09"}
    assert db.scalar(select(func.count()).select_from(TemplateImportacao)) == 1


def test_bi_existente_funciona_sobre_os_itens_importados(db):
    itens = DatasetTransactionSource(db, LOJA).get_items(*AGOSTO)
    kpis = Relatorio(Vendas(itens), Trocas(itens)).kpis()

    por_documento = {}
    for item in itens:
        por_documento.setdefault(item.document_id, set()).add(item.document_total)
    assert all(len(totais) == 1 for totais in por_documento.values())
    assert kpis.faturamento_bruto > 0
    assert kpis.total_trocas > 0
    assert kpis.qtd_tickets > 500
    assert all(i.time is not None for i in itens)


def test_equipe_da_demo_conta_a_historia_dos_vendedores(db):
    fonte = FonteEquipeDatasets(db, LOJA)

    resultado = resultado_equipe(fonte, *AGOSTO, metas=metas_para_calculo(db, LOJA, "2026-08"))
    nomes = [v.vendedor for v in resultado.vendedores if not v.sem_vendedor]
    por_nome = {v.vendedor: v for v in resultado.vendedores}

    assert nomes[0] == "Mariana Souza"
    assert nomes[-1] == "Diego Alves"
    assert por_nome["Rafael Mendes"].pa == max(v.pa for v in resultado.vendedores if not v.sem_vendedor)
    assert por_nome["Mariana Souza"].atingimento is not None
    assert resultado.indisponivel[0].indicador == "conversao_contatos"


def test_relatorio_de_exemplo_confere_com_os_itens_do_mes():
    nome, conteudo = relatorio_exemplo(HOJE)

    resultado = aplicar(extrair(conteudo, nome), mapeamento_do_exemplo())

    assert nome == "vendas-por-vendedor-agosto.xlsx"
    assert resultado.validacao.status == "conferido"
    assert resultado.periodo == AGOSTO
