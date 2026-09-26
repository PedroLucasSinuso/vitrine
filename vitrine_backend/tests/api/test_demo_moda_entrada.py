import pytest

from app.application.utils.security import hash_password
from app.domain.models.configuracao import Configuracao
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario


@pytest.fixture
def demo_moda(db_session, monkeypatch):
    monkeypatch.setattr("app.api.routes.auth.resetar_se_necessario", lambda *a, **k: False)
    empresa = Empresa(nome="Vitrine Moda", slug="demo-moda", status="ativa", segmento="moda", modo="upload")
    db_session.add(empresa)
    db_session.flush()
    db_session.add(Configuracao(empresa_id=empresa.id, chave="erp_adapter", valor="demo"))
    db_session.add(Usuario(
        username="demo.moda", nome_exibicao="Demo Moda", role="admin",
        hashed_password=hash_password("demo1234"), empresa_id=empresa.id,
    ))
    db_session.commit()
    return empresa


def test_perfis_lista_so_os_provisionados(client, demo_moda):
    assert client.get("/auth/demo/perfis").json() == {"perfis": ["moda"]}


def test_entra_na_demo_de_moda_e_ve_o_perfil_de_moda(client, demo_moda):
    token = client.post("/auth/demo", json={"perfil": "moda"}).json()["access_token"]

    perfil = client.get("/empresa/perfil", headers={"Authorization": f"Bearer {token}"}).json()

    assert perfil["segmento"] == "moda"
    assert perfil["modo"] == "upload"
    assert "equipe" in perfil["modulos"] and "importacao" in perfil["modulos"]
    assert "busca" not in perfil["modulos"]


def test_perfil_inexistente_ou_nao_provisionado_da_404(client, demo_moda):
    assert client.post("/auth/demo", json={"perfil": "farmacia"}).status_code == 404
    assert client.post("/auth/demo", json={"perfil": "supermercado"}).status_code == 404


def test_relatorio_de_exemplo_para_baixar(client, demo_moda):
    token = client.post("/auth/demo", json={"perfil": "moda"}).json()["access_token"]

    resposta = client.get("/importacoes/exemplo", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 200
    assert resposta.content.startswith(b"PK")
    assert "vendas-por-vendedor-" in resposta.headers["content-disposition"]


def test_bi_do_modo_upload_le_os_itens_importados_e_nao_o_erp(client, db_session, demo_moda):
    from datetime import date

    from app.application.demo_moda import popular_moda

    popular_moda(db_session, demo_moda.id, hoje=date(2026, 9, 26))
    db_session.commit()
    token = client.post("/auth/demo", json={"perfil": "moda"}).json()["access_token"]

    ranking = client.get(
        "/bi/ranking", headers={"Authorization": f"Bearer {token}"},
        params={"data_inicio": "2026-08-01", "data_fim": "2026-08-31", "top": 5},
    ).json()

    produtos_de_moda = {nome for modelos in __import__("app.adapters.demo.moda", fromlist=["CATALOGO"]).CATALOGO.values() for nome, _ in modelos}
    assert ranking
    assert {item["produto"] for item in ranking} <= produtos_de_moda
