from datetime import date

import pytest

from app.api.deps import get_fonte_equipe
from app.application.equipe.fonte import FonteEquipeErp
from app.application.utils.security import hash_password
from app.main import app
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario
from tests.api.conftest import get_token
from vitrine_core.models.transaction import OperationType

SET1, SET2 = date(2026, 9, 1), date(2026, 9, 2)
PERIODO = {"data_inicio": "2026-09-01", "data_fim": "2026-09-02"}


def _usuario_em(db_session, slug, segmento, role="supervisor"):
    empresa = Empresa(nome=slug, slug=slug, status="ativa", segmento=segmento)
    db_session.add(empresa)
    db_session.flush()
    db_session.add(Usuario(
        username=f"{role}.{slug}", nome_exibicao=slug, role=role,
        hashed_password=hash_password("senha123"), empresa_id=empresa.id,
    ))
    db_session.commit()
    return f"{role}.{slug}"


@pytest.fixture
def cabecalho_moda(client, db_session):
    usuario = _usuario_em(db_session, "loja-moda", "moda")
    return {"Authorization": f"Bearer {get_token(client, usuario)}"}


@pytest.fixture
def com_vendas(transaction_source, criar_item):
    app.dependency_overrides[get_fonte_equipe] = lambda: FonteEquipeErp(transaction_source)
    transaction_source.items_por_data = {
        SET1: [criar_item("V1", SET1, 10, 100.0, qtd=2), criar_item("V2", SET1, 11, 50.0)],
        SET2: [
            criar_item("V3", SET2, 15, 150.0, qtd=3),
            criar_item("T1", SET2, 16, -30.0, operacao=OperationType.RETURN),
        ],
    }
    return transaction_source


def test_equipe_do_erp_sem_vendedor_cai_no_balde_sem_vendedor(client, cabecalho_moda, com_vendas):
    resposta = client.get("/bi/equipe", params=PERIODO, headers=cabecalho_moda)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["loja"] == {
        "faturamento_bruto": 300.0, "trocas": 30.0, "faturamento_liquido": 270.0,
        "atendimentos": 3, "atendimentos_somados_por_vendedor": False,
        "ticket_medio": 100.0, "pa": 2.0,
        "meta": None, "atingimento": None, "projecao": None,
    }
    assert [(v["vendedor"], v["sem_vendedor"]) for v in corpo["vendedores"]] == [("Sem vendedor", True)]
    assert [i["indicador"] for i in corpo["indisponivel"]] == ["conversao_contatos"]
    assert corpo["periodo_anterior"] is None


def test_serie_e_mix_do_balde_sem_vendedor(client, cabecalho_moda, com_vendas):
    serie = client.get("/bi/equipe/serie", params=PERIODO, headers=cabecalho_moda).json()
    mix = client.get("/bi/equipe/mix", params=PERIODO, headers=cabecalho_moda).json()

    assert [(p["data"], p["faturamento_bruto"]) for p in serie] == [("2026-09-01", 150.0), ("2026-09-02", 150.0)]
    assert mix == [{"grupo": "GRUPO", "familia": "FAMILIA", "receita": 300.0, "participacao": 1.0}]


def test_supermercado_nao_tem_o_modulo_equipe(client, db_session, transaction_source):
    usuario = _usuario_em(db_session, "mercado", "supermercado")
    cabecalho = {"Authorization": f"Bearer {get_token(client, usuario)}"}

    assert client.get("/bi/equipe", params=PERIODO, headers=cabecalho).status_code == 404


def test_operador_nao_acessa_equipe(client, db_session, transaction_source):
    usuario = _usuario_em(db_session, "moda-op", "moda", role="operador")
    cabecalho = {"Authorization": f"Bearer {get_token(client, usuario)}"}

    assert client.get("/bi/equipe", params=PERIODO, headers=cabecalho).status_code == 403


@pytest.mark.parametrize("params", [
    {"data_inicio": "2026-09-10", "data_fim": "2026-09-01"},
    {"data_inicio": "2026-01-01", "data_fim": "2026-09-01"},
])
def test_periodo_invalido(client, cabecalho_moda, transaction_source, params):
    assert client.get("/bi/equipe", params=params, headers=cabecalho_moda).status_code == 400


def test_modulo_e_checado_antes_de_abrir_o_erp(client, db_session):
    usuario = _usuario_em(db_session, "mercado-sem-erp", "supermercado")
    cabecalho = {"Authorization": f"Bearer {get_token(client, usuario)}"}

    assert client.get("/bi/equipe", params=PERIODO, headers=cabecalho).status_code == 404
