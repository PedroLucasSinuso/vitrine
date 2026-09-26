from datetime import date

import pytest

from app.application.utils.security import hash_password
from app.core.config import settings
from app.domain.models.usuario import Usuario
from tests.api.conftest import get_token
from tests.api.test_importacao import _cabecalho, _enviar, _mapeamento
from tests.importacao import relatorios as rel

SETEMBRO = {"data_inicio": "2026-09-01", "data_fim": "2026-09-30"}


@pytest.fixture(autouse=True)
def pasta_de_importacao(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "importacao_dir", str(tmp_path / "importacoes"))


@pytest.fixture
def loja(client, db_session):
    admin = _cabecalho(client, db_session, "loja-metas", role="admin")
    empresa_id = db_session.query(Usuario).filter_by(username="admin.loja-metas").one().empresa_id
    db_session.add(Usuario(
        username="sup.loja-metas", nome_exibicao="Sup", role="supervisor",
        hashed_password=hash_password("senha123"), empresa_id=empresa_id,
    ))
    db_session.commit()
    supervisor = {"Authorization": f"Bearer {get_token(client, 'sup.loja-metas')}"}
    corpo = _enviar(client, admin, rel.vendedores_xlsx()).json()
    client.put(f"/importacoes/{corpo['id']}/mapeamento", headers=admin, json=_mapeamento(rel.linha_cabecalho_vendedores()))
    client.post(f"/importacoes/{corpo['id']}/confirmar", headers=admin)
    return admin, supervisor


def _vendedores(client, cabecalho):
    equipe = client.get("/bi/equipe", headers=cabecalho, params=SETEMBRO).json()
    return {v["vendedor"]: v for v in equipe["vendedores"]}, equipe


def test_metas_aparecem_na_equipe_com_atingimento_e_comissao(client, loja):
    admin, supervisor = loja

    resposta = client.put("/metas/2026-09", headers=admin, json=[
        {"vendedor": "MARIANA SOUZA", "valor_meta": 10000, "percentual_comissao": 2},
        {"vendedor": "carlos lima", "valor_meta": 5000},
    ])
    vendedores, equipe = _vendedores(client, supervisor)

    assert resposta.status_code == 200
    assert equipe["competencia"] == "2026-09"
    assert vendedores["MARIANA SOUZA"]["meta"] == 10000.0
    assert vendedores["MARIANA SOUZA"]["atingimento"] == round(8620.5 / 10000, 4)
    assert vendedores["MARIANA SOUZA"]["comissao_estimada"] == round(8620.5 * 0.02, 2)
    assert vendedores["CARLOS LIMA"]["meta"] == 5000.0
    assert vendedores["JULIA PEREIRA"]["meta"] is None
    assert equipe["loja"]["meta"] == 15000.0


def test_supervisor_ve_mas_nao_edita_metas(client, loja):
    _, supervisor = loja

    assert client.get("/metas/2026-09", headers=supervisor).status_code == 200
    assert client.put("/metas/2026-09", headers=supervisor, json=[]).status_code == 403


def test_listagem_traz_vendedores_conhecidos_dos_dados(client, loja):
    admin, _ = loja

    corpo = client.get("/metas/2026-09", headers=admin).json()

    assert corpo["vendedores_conhecidos"] == ["ANA COSTA", "CARLOS LIMA", "JULIA PEREIRA", "MARIANA SOUZA"]


def test_copiar_metas_do_mes_anterior(client, loja):
    admin, _ = loja
    client.put("/metas/2026-08", headers=admin, json=[{"vendedor": "ANA COSTA", "valor_meta": 3000, "percentual_comissao": 1}])

    corpo = client.post("/metas/2026-09/copiar-de/2026-08", headers=admin).json()

    assert [(m["vendedor"], float(m["valor_meta"])) for m in corpo["metas"]] == [("ANA COSTA", 3000.0)]


@pytest.mark.parametrize("competencia", ["2026-13", "setembro", "2026-9"])
def test_competencia_invalida(client, loja, competencia):
    admin, _ = loja

    assert client.get(f"/metas/{competencia}", headers=admin).status_code == 400


def test_meta_negativa_e_recusada(client, loja):
    admin, _ = loja

    assert client.put("/metas/2026-09", headers=admin, json=[{"vendedor": "ANA", "valor_meta": -1}]).status_code == 422


def test_alias_junta_dois_nomes_no_ranking(client, loja):
    admin, supervisor = loja

    resposta = client.put("/vendedores/alias", headers=admin, json=[{"nome_origem": "ANA COSTA", "vendedor": "JULIA PEREIRA"}])
    vendedores, _ = _vendedores(client, supervisor)

    assert resposta.status_code == 200
    assert "ANA COSTA" not in vendedores
    assert vendedores["JULIA PEREIRA"]["faturamento_bruto"] == round(7402.90 + 3100.00, 2)
    assert client.get("/vendedores/alias", headers=supervisor).json() == [{"nome_origem": "ANA COSTA", "vendedor": "JULIA PEREIRA"}]


def test_supermercado_nao_tem_metas(client, db_session):
    mercado = _cabecalho(client, db_session, "mercado-metas", segmento="supermercado", role="admin")

    assert client.get("/metas/2026-09", headers=mercado).status_code == 404
