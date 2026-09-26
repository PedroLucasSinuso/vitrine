from datetime import date

import pytest

from app.application.demo_equipe import popular_equipe
from app.application.utils.security import hash_password
from app.domain.models.configuracao import Configuracao
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario
from tests.api.conftest import get_token

HOJE = date.today()
INICIO = HOJE.replace(day=1).isoformat()
PERIODO = {"data_inicio": INICIO, "data_fim": HOJE.isoformat()}


@pytest.fixture
def equipe(client, db_session, monkeypatch):
    monkeypatch.setattr("app.api.routes.auth.resetar_se_necessario", lambda *a, **k: False)
    empresa = Empresa(nome="Vitrine Equipe", slug="demo-equipe", status="ativa", segmento="equipe", modo="upload")
    db_session.add(empresa)
    db_session.flush()
    db_session.add(Configuracao(empresa_id=empresa.id, chave="erp_adapter", valor="demo"))
    db_session.add(Usuario(
        username="demo.equipe", nome_exibicao="Demo", role="admin",
        hashed_password=hash_password("demo1234"), empresa_id=empresa.id,
    ))
    db_session.commit()
    popular_equipe(db_session, empresa.id)
    db_session.commit()
    token = client.post("/auth/demo", json={"perfil": "equipe"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_entrada_na_demo_equipe_abre_so_com_modulos_de_equipe(client, equipe):
    perfil = client.get("/empresa/perfil", headers=equipe).json()

    assert perfil["segmento"] == "equipe"
    assert set(perfil["modulos"]) == {"equipe", "metas", "importacao"}


def test_bi_de_vendas_nao_existe_para_a_equipe(client, equipe):
    assert client.get("/bi/grade", headers=equipe, params=PERIODO).status_code == 404


def test_equipe_do_mes_traz_rotatividade_e_resumo(client, equipe):
    corpo = client.get("/bi/equipe", headers=equipe, params=PERIODO).json()

    assert corpo["periodo_anterior"] is not None
    assert corpo["equipe"]["vendedores_ativos"] >= 6
    assert corpo["equipe"]["vendedores_ativos_anterior"] >= 6
    novos = {v["vendedor"] for v in corpo["vendedores"] if v["novo"]}
    assert novos == set(corpo["equipe"]["entradas"])


def test_detalhe_do_vendedor_so_traz_os_blocos_que_existem(client, equipe):
    resposta = client.get("/bi/equipe/vendedor", headers=equipe, params={**PERIODO, "nome": "mariana souza"})

    corpo = resposta.json()
    assert resposta.status_code == 200
    assert corpo["indicadores"]["vendedor"] == "MARIANA SOUZA"
    assert corpo["posicao"] == 1
    assert corpo["comparacao_loja"]["ticket_medio"] is not None
    assert corpo["indicadores"]["conversao"] is not None
    assert len(corpo["serie_mensal"]) == 6
    assert corpo["serie_diaria"] is None and corpo["mix"] is None
    assert {i["indicador"] for i in corpo["indisponivel"]} == {"serie_diaria", "mix_categoria"}


def test_vendedor_sem_contatos_fica_sem_conversao(client, equipe):
    corpo = client.get("/bi/equipe/vendedor", headers=equipe, params={**PERIODO, "nome": "Patrícia Nunes"}).json()

    assert corpo["indicadores"]["conversao"] is None
    assert corpo["indicadores"]["contatos"] is None


def test_detalhe_de_vendedor_inexistente_da_404(client, equipe):
    assert client.get("/bi/equipe/vendedor", headers=equipe, params={**PERIODO, "nome": "Fulano"}).status_code == 404


def test_serie_mensal_da_equipe_e_do_vendedor(client, equipe):
    toda = client.get("/bi/equipe/serie-mensal", headers=equipe, params={"data_fim": HOJE.isoformat(), "meses": 6}).json()
    lucas = client.get("/bi/equipe/serie-mensal", headers=equipe, params={"data_fim": HOJE.isoformat(), "meses": 6, "vendedor": "lucas ferreira"}).json()

    assert len(toda) == 6
    assert toda[-1]["vendedores_ativos"] >= 6
    assert lucas[0]["ausente"] is False and lucas[-1]["ausente"] is True


@pytest.mark.parametrize("meses", [1, 13])
def test_meses_fora_do_limite(client, equipe, meses):
    resposta = client.get("/bi/equipe/serie-mensal", headers=equipe, params={"data_fim": HOJE.isoformat(), "meses": meses})

    assert resposta.status_code == 422


def test_exemplo_da_demo_equipe_vem_no_layout_de_relatorio_por_vendedor(client, equipe):
    resposta = client.get("/importacoes/exemplo", headers=equipe)

    assert resposta.status_code == 200
    assert resposta.content.startswith(b"PK")
