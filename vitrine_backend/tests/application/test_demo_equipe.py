from datetime import date

import pytest
from sqlalchemy import func, select

from app.application.demo_equipe import popular_equipe, relatorio_exemplo
from app.application.equipe.fonte import FonteEquipeDatasets
from app.application.equipe.metas import metas_para_calculo
from app.application.equipe.servico import resultado_equipe, serie_mensal_equipe, serie_mensal_vendedor
from app.application.importacao.aplicacao import aplicar
from app.application.importacao.exemplo import mapeamento_do_exemplo
from app.application.importacao.extracao import extrair
from app.domain.models.importacao import Dataset
from app.domain.segmentos import modulos_da_empresa
from app.domain.enums import ModoOperacao, Segmento
from tests.bancos import BANCOS, sessao_em_banco_limpo

HOJE = date(2026, 9, 26)
LOJA = 1
SETEMBRO = (date(2026, 9, 1), date(2026, 9, 26))
AGOSTO = (date(2026, 8, 1), date(2026, 8, 31))


@pytest.fixture(params=BANCOS)
def db(request):
    for sessao in sessao_em_banco_limpo(request.param, {LOJA: "demo-equipe"}):
        popular_equipe(sessao, LOJA, hoje=HOJE)
        sessao.commit()
        yield sessao


def _por_nome(resultado):
    return {v.vendedor: v for v in resultado.vendedores}


def test_so_relatorios_por_periodo_e_contatos_nunca_itens(db):
    tipos = set(db.scalars(select(Dataset.tipo).distinct()))

    assert tipos == {"vendas_vendedor_periodo", "contatos_vendedor"}
    assert db.scalar(select(func.count()).select_from(Dataset).where(Dataset.tipo == "vendas_vendedor_periodo")) == 6


def test_perfil_da_demo_nao_tem_nenhum_modulo_de_bi_de_vendas():
    modulos = modulos_da_empresa(Segmento.EQUIPE, ModoOperacao.UPLOAD, {"vendas_vendedor_periodo"})

    assert modulos == {"equipe", "metas", "importacao"}


def test_setembro_compara_com_agosto_e_conta_a_rotatividade(db):
    fonte = FonteEquipeDatasets(db, LOJA)

    resultado = resultado_equipe(fonte, *SETEMBRO, metas=metas_para_calculo(db, LOJA, "2026-09"))
    vendedores = _por_nome(resultado)

    assert (resultado.periodo_anterior.inicio, resultado.periodo_anterior.fim) == AGOSTO
    assert resultado.comparacao_parcial is True
    assert resultado.equipe.entradas == ["THIAGO BARROS"]
    assert resultado.equipe.saidas == ["LUCAS FERREIRA"]
    assert vendedores["THIAGO BARROS"].novo is True
    assert vendedores["MARIANA SOUZA"].variacao_liquido is None
    assert vendedores["MARIANA SOUZA"].variacao_ticket_medio is not None
    assert vendedores["MARIANA SOUZA"].atingimento is not None


def test_mes_fechado_compara_com_mes_fechado(db):
    resultado = resultado_equipe(FonteEquipeDatasets(db, LOJA), *AGOSTO)

    assert (resultado.periodo_anterior.inicio, resultado.periodo_anterior.fim) == (date(2026, 7, 1), date(2026, 7, 31))
    assert _por_nome(resultado)["DIEGO ALVES"].variacao_liquido < -0.5


def test_conversao_so_existe_para_quem_tem_contatos(db):
    resultado = resultado_equipe(FonteEquipeDatasets(db, LOJA), *AGOSTO)
    vendedores = _por_nome(resultado)

    assert vendedores["MARIANA SOUZA"].conversao is not None
    assert vendedores["PATRÍCIA NUNES"].conversao is None


def test_serie_mensal_da_equipe_e_do_vendedor_novato(db):
    fonte = FonteEquipeDatasets(db, LOJA)

    equipe = serie_mensal_equipe(fonte, HOJE, 6, {})
    beatriz = serie_mensal_vendedor(fonte, HOJE, 6, "BEATRIZ LIMA", {})

    assert len(equipe) == 6 and equipe[-1].parcial is True
    assert equipe[0].vendedores_ativos == 6 and equipe[-1].vendedores_ativos == 7
    assert [p.ausente for p in beatriz] == [True, True, True, False, False, False]


def test_relatorio_de_exemplo_confere_e_bate_com_o_dataset_do_mes(db):
    nome, conteudo = relatorio_exemplo(HOJE)
    lido = aplicar(extrair(conteudo, nome), mapeamento_do_exemplo())
    guardado = {v.vendedor: v for v in FonteEquipeDatasets(db, LOJA).vendedor_periodo(*AGOSTO)}

    assert lido.validacao.status == "conferido"
    assert lido.periodo == AGOSTO
    assert {r["vendedor"] for r in lido.registros} == set(guardado)
    assert all(float(r["faturamento_bruto"]) == float(guardado[r["vendedor"]].faturamento_bruto) for r in lido.registros)
