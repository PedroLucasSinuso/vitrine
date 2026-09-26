import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_db, require_modulo
from app.application.utils.jwt_handler import create_access_token
from app.application.utils.security import hash_password
from app.domain.models.empresa import Empresa
from app.domain.models.usuario import Usuario
from app.domain.segmentos import MODULOS_CATALOGO
from tests.api.conftest import get_token

MODULOS_ATUAIS = {
    "dashboard", "receita", "ranking", "curva_abc", "trocas", "perdas_consumo",
    "temporal", "sku", "busca", "produtos", "inventario", "etiquetas",
}


def _empresa_com_usuario(db_session, slug, segmento="supermercado", modo="legado", role="operador"):
    empresa = Empresa(nome=f"Loja {slug}", slug=slug, status="ativa", segmento=segmento, modo=modo)
    db_session.add(empresa)
    db_session.flush()
    db_session.add(Usuario(
        username=f"user.{slug}", nome_exibicao="Usuário", role=role,
        hashed_password=hash_password("senha123"), empresa_id=empresa.id,
    ))
    db_session.commit()
    return empresa


def _perfil(client, username):
    token = get_token(client, username)
    return client.get("/empresa/perfil", headers={"Authorization": f"Bearer {token}"})


def test_empresa_existente_e_supermercado_legado_com_os_modulos_de_hoje(client, db_session, empresa_padrao, usuario_operador):
    resposta = _perfil(client, "operador1")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["segmento"] == "supermercado"
    assert corpo["modo"] == "legado"
    assert set(corpo["modulos"]) == MODULOS_ATUAIS
    assert corpo["rotulos"]["grupo"] == "Grupo"


@pytest.mark.parametrize("role", ["operador", "supervisor", "admin"])
def test_qualquer_role_da_empresa_le_o_perfil(client, db_session, role):
    _empresa_com_usuario(db_session, f"loja-{role}", role=role)

    assert _perfil(client, f"user.loja-{role}").status_code == 200


def test_moda_troca_rotulos_e_nao_tem_perdas(client, db_session):
    _empresa_com_usuario(db_session, "moda", segmento="moda")

    corpo = _perfil(client, "user.moda").json()

    assert corpo["rotulos"] == {
        "grupo": "Departamento", "grupos": "Departamentos",
        "familia": "Categoria", "familias": "Categorias",
        "documento": "Atendimento",
    }
    assert "perdas_consumo" not in corpo["modulos"]
    assert {"equipe", "metas", "grade"} <= set(corpo["modulos"])


def test_modo_upload_remove_modulos_que_dependem_do_erp(client, db_session):
    _empresa_com_usuario(db_session, "upload", segmento="varejo", modo="upload")

    modulos = set(_perfil(client, "user.upload").json()["modulos"])

    assert not modulos & MODULOS_CATALOGO
    assert "perdas_consumo" not in modulos
    assert "equipe" in modulos


def test_perfil_exige_autenticacao(client):
    assert client.get("/empresa/perfil").status_code == 401


def test_super_admin_sem_empresa_recebe_404(client, db_session):
    usuario = Usuario(
        username="root", nome_exibicao="Root", role="super_admin",
        hashed_password=hash_password("senha123"), empresa_id=None,
    )
    db_session.add(usuario)
    db_session.commit()

    assert _perfil(client, "root").status_code == 404


@pytest.fixture
def cliente_com_rota_de_modulo(db_session):
    rotas = APIRouter()

    @rotas.get("/equipe")
    def equipe(_=Depends(require_modulo("equipe"))):
        return {"ok": True}

    app = FastAPI()
    app.include_router(rotas)
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _token_de(db_session, username):
    usuario = db_session.query(Usuario).filter_by(username=username).one()
    return create_access_token(
        {"sub": usuario.username, "role": usuario.role},
        user_id=usuario.id,
        token_version=usuario.token_version,
        empresa_id=usuario.empresa_id,
    )


def test_require_modulo_libera_quando_o_segmento_tem_o_modulo(cliente_com_rota_de_modulo, db_session):
    _empresa_com_usuario(db_session, "moda-ok", segmento="moda")
    token = _token_de(db_session, "user.moda-ok")

    resposta = cliente_com_rota_de_modulo.get("/equipe", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 200


def test_require_modulo_responde_404_quando_o_segmento_nao_tem(cliente_com_rota_de_modulo, db_session):
    _empresa_com_usuario(db_session, "mercado", segmento="supermercado")
    token = _token_de(db_session, "user.mercado")

    resposta = cliente_com_rota_de_modulo.get("/equipe", headers={"Authorization": f"Bearer {token}"})

    assert resposta.status_code == 404
