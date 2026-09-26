from datetime import date, datetime, timedelta, timezone
from decimal import Decimal as D

import pytest

from app.application.equipe.fonte import FonteEquipeDatasets
from app.application.importacao.persistencia import gravar_dataset
from app.application.limpeza import limpar_registros_antigos
from app.domain.models.importacao import ArquivoImportado
from tests.bancos import BANCOS, sessao_em_banco_limpo
from vitrine_core.datasets.tipos import Operacao, TipoDataset

LOJA = 1
SET = (date(2026, 9, 1), date(2026, 9, 30))


@pytest.fixture(params=BANCOS)
def db(request):
    yield from sessao_em_banco_limpo(request.param, {LOJA: "loja"})


def _vendedores(db, periodo, linhas, nome="rel.xlsx"):
    registros = [
        {"vendedor": v, "atendimentos": a, "pecas": D(p), "faturamento_bruto": D(b), "trocas": D("0")}
        for v, a, p, b in linhas
    ]
    gravar_dataset(db, LOJA, TipoDataset.VENDAS_VENDEDOR_PERIODO, periodo, registros, nome)
    db.commit()


def _por_vendedor(linhas):
    return {l.vendedor: l for l in linhas}


def test_relatorio_mensal_so_entra_quando_o_periodo_pedido_o_contem(db):
    _vendedores(db, SET, [("Ana", 10, "20", "1000")])
    fonte = FonteEquipeDatasets(db, LOJA)

    assert _por_vendedor(fonte.vendedor_periodo(*SET))["Ana"].faturamento_bruto == D("1000")
    assert fonte.vendedor_periodo(date(2026, 9, 1), date(2026, 9, 15)) == []


def test_datasets_sobrepostos_vence_o_mais_recente(db):
    _vendedores(db, SET, [("Ana", 10, "20", "1000")], nome="antigo.xlsx")
    _vendedores(db, SET, [("Ana", 12, "24", "1200")], nome="corrigido.xlsx")

    linhas = FonteEquipeDatasets(db, LOJA).vendedor_periodo(*SET)

    assert [l.faturamento_bruto for l in linhas] == [D("1200")]


def test_quinzenas_somam_no_mes(db):
    _vendedores(db, (date(2026, 9, 1), date(2026, 9, 15)), [("Ana", 5, "10", "500")])
    _vendedores(db, (date(2026, 9, 16), date(2026, 9, 30)), [("Ana", 6, "12", "700")])

    linhas = FonteEquipeDatasets(db, LOJA).vendedor_periodo(*SET)

    assert sum(l.faturamento_bruto for l in linhas) == D("1200")


def test_itens_tem_prioridade_e_liberam_serie_e_mix(db):
    _vendedores(db, SET, [("Ana", 99, "99", "9999")])
    itens = [
        {"documento": "1", "data": date(2026, 9, 2), "operacao": Operacao.VENDA, "quantidade": D("2"),
         "valor": D("100"), "vendedor": "Ana", "grupo": "FEM", "familia": "VESTIDOS"},
        {"documento": "2", "data": date(2026, 9, 3), "operacao": Operacao.VENDA, "quantidade": D("1"),
         "valor": D("50"), "vendedor": "Bruno"},
    ]
    gravar_dataset(db, LOJA, TipoDataset.ITENS_VENDA, (date(2026, 9, 2), date(2026, 9, 3)), itens, "itens.xlsx")
    db.commit()
    fonte = FonteEquipeDatasets(db, LOJA)

    linhas = _por_vendedor(fonte.vendedor_periodo(*SET))

    assert linhas["Ana"].faturamento_bruto == D("100")
    assert fonte.atendimentos_loja(*SET) == 2
    assert fonte.diarias(*SET) is not None
    assert fonte.itens(*SET) is not None


def test_sem_datasets_nao_ha_tipos(db):
    fonte = FonteEquipeDatasets(db, LOJA)

    assert fonte.tipos == set()
    assert fonte.diarias(*SET) is None


def test_limpeza_apaga_arquivo_original_vencido(db, tmp_path):
    arquivo_fisico = tmp_path / "original.xlsx"
    arquivo_fisico.write_bytes(b"conteudo")
    agora = datetime(2026, 10, 30, tzinfo=timezone.utc)
    db.add(ArquivoImportado(
        empresa_id=LOJA, nome_original="original.xlsx", formato="xlsx", tamanho=8, sha256="x" * 64,
        caminho=str(arquivo_fisico), status="confirmado", expira_em=agora - timedelta(days=1),
    ))
    db.commit()

    resultado = limpar_registros_antigos(db, agora=agora)

    assert resultado.arquivos_importados == 1
    assert not arquivo_fisico.exists()
    assert db.query(ArquivoImportado).one().caminho is None
