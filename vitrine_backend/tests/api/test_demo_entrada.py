"""Entrada pública na demonstração (botão "Ver demo" da landing)."""

import pytest

from app.application.utils.jwt_handler import decode_access_token
from app.application.demo_provisioner import SLUG_DEMO, USUARIO_DEMO, senha_padrao
from app.application.utils.security import hash_password
from app.domain.models.configuracao import Configuracao
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario


@pytest.fixture
def resets(monkeypatch):
    """Conta quantos resets a rota disparou, sem tocar o banco de verdade.

    ``resetar_se_necessario`` abre a própria ``SqliteSession`` (arquivo),
    e não a de memória dos testes — chamá-lo aqui mexeria no banco de
    desenvolvimento da máquina.
    """
    chamadas = []
    monkeypatch.setattr(
        "app.api.routes.auth.resetar_se_necessario",
        lambda *a, **kw: chamadas.append(1) or True,
    )
    return chamadas


@pytest.fixture
def tenant_demo(db_session):
    empresa = Empresa(nome="Vitrine Demo", slug=SLUG_DEMO, status="ativa")
    db_session.add(empresa)
    db_session.flush()
    db_session.add(Configuracao(empresa_id=empresa.id, chave="erp_adapter", valor="demo"))
    db_session.add(
        Usuario(
            username=USUARIO_DEMO,
            nome_exibicao="Demonstração (Admin)",
            role="admin",
            hashed_password=hash_password(senha_padrao()),
            token_version=0,
            empresa_id=empresa.id,
        )
    )
    db_session.commit()
    return empresa


def test_status_diz_indisponivel_sem_tenant_de_demo(client):
    assert client.get("/auth/demo").json() == {"disponivel": False}


def test_status_diz_disponivel_com_tenant_de_demo(client, tenant_demo):
    assert client.get("/auth/demo").json() == {"disponivel": True}


def test_entrada_devolve_token_do_tenant_de_demo(client, tenant_demo, resets):
    resp = client.post("/auth/demo")

    assert resp.status_code == 200
    claims = decode_access_token(resp.json()["access_token"])
    assert claims["sub"] == USUARIO_DEMO
    assert claims["empresa_id"] == tenant_demo.id
    assert claims["role"] == "admin", "o visitante precisa alcançar todas as telas"


def test_entrada_reseta_antes_de_liberar_o_visitante(client, tenant_demo, resets):
    client.post("/auth/demo")

    assert resets == [1], "sem o reset, o visitante herda a bagunça do anterior"


def test_token_da_demo_abre_as_rotas_protegidas(client, tenant_demo, resets):
    token = client.post("/auth/demo").json()["access_token"]

    resp = client.get("/produtos/", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200


def test_sem_tenant_de_demo_a_entrada_da_404(client, resets):
    resp = client.post("/auth/demo")

    assert resp.status_code == 404
    assert resets == [], "não faz sentido resetar o que não existe"


def test_empresa_com_slug_demo_mas_erp_real_nao_abre(client, db_session, resets):
    """Guarda-corpo: 'demo' é um slug como outro qualquer.

    Um cliente que registrasse esse slug não pode virar demonstração
    pública — o que decide é o ``erp_adapter``, não o nome.
    """
    empresa = Empresa(nome="Mercado Demo Ltda", slug=SLUG_DEMO, status="ativa")
    db_session.add(empresa)
    db_session.flush()
    db_session.add(Configuracao(empresa_id=empresa.id, chave="erp_adapter", valor="alterdata"))
    db_session.commit()

    assert client.get("/auth/demo").json() == {"disponivel": False}
    assert client.post("/auth/demo").status_code == 404
    assert resets == []
