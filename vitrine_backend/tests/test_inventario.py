"""Testes para os endpoints de inventÃ¡rio multi-usuÃ¡rio."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db, get_current_user, require_supervisor
from app.api.routes.inventario import router
from app.infrastructure.db.database import Base
from app.application.utils.security import hash_password
from app.domain.models.usuario import Usuario

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session(reset_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def usuario_admin(db_session):
    user = Usuario(
        username="admin1",
        nome_exibicao="Admin",
        role="admin",
        hashed_password=hash_password("senha123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def usuario_operador(db_session):
    user = Usuario(
        username="oper1",
        nome_exibicao="Operador",
        role="operador",
        hashed_password=hash_password("senha123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def app(db_session, usuario_admin, usuario_operador):
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return usuario_admin

    def override_require_supervisor():
        return usuario_admin

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_supervisor] = override_require_supervisor
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app)


class TestInventario:
    def test_criar_sessao(self, client):
        resp = client.post("/admin/inventario/sessoes", json={"nome": "InventÃ¡rio 01"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["nome"] == "InventÃ¡rio 01"
        assert data["status"] == "ativa"
        assert len(data["codigo_convite"]) == 6

    def test_criar_sessao_sem_nome(self, client):
        resp = client.post("/admin/inventario/sessoes", json={"nome": ""})
        assert resp.status_code == 201
        assert resp.json()["nome"] == ""

    def test_listar_sessoes(self, client):
        client.post("/admin/inventario/sessoes", json={"nome": "SessÃ£o A"})
        client.post("/admin/inventario/sessoes", json={"nome": "SessÃ£o B"})
        resp = client.get("/admin/inventario/sessoes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_entrar_sessao_por_codigo(self, client):
        criar = client.post("/admin/inventario/sessoes", json={"nome": "Minha SessÃ£o"}).json()
        codigo = criar["codigo_convite"]
        resp = client.post("/admin/inventario/sessoes/entrar", json={"codigo_convite": codigo})
        assert resp.status_code == 201
        assert resp.json()["id"] == criar["id"]

    def test_entrar_sessao_invalida(self, client):
        resp = client.post("/admin/inventario/sessoes/entrar", json={"codigo_convite": "XXXXXX"})
        assert resp.status_code == 404

    def test_adicionar_item(self, client):
        sessao = client.post("/admin/inventario/sessoes", json={"nome": "Teste"}).json()
        resp = client.post(
            f"/admin/inventario/sessoes/{sessao['id']}/itens",
            json={"codigo": "123456", "nome": "Produto A", "grupo": "Alimentos", "familia": "Bebidas", "quantidade": 2},
        )
        assert resp.status_code == 201

        itens = client.get(f"/admin/inventario/sessoes/{sessao['id']}/itens").json()
        assert len(itens) == 1
        assert itens[0]["codigo"] == "123456"
        assert itens[0]["quantidade"] == 2

    def test_adicionar_mesmo_item_soma(self, client):
        sessao = client.post("/admin/inventario/sessoes", json={"nome": "Teste"}).json()
        sid = sessao["id"]
        client.post(f"/admin/inventario/sessoes/{sid}/itens", json={"codigo": "123", "nome": "X", "grupo": "G", "familia": "F", "quantidade": 1})
        client.post(f"/admin/inventario/sessoes/{sid}/itens", json={"codigo": "123", "nome": "X", "grupo": "G", "familia": "F", "quantidade": 3})
        itens = client.get(f"/admin/inventario/sessoes/{sid}/itens").json()
        assert len(itens) == 1
        assert itens[0]["quantidade"] == 4

    def test_atualizar_item(self, client):
        sessao = client.post("/admin/inventario/sessoes", json={"nome": "Teste"}).json()
        sid = sessao["id"]
        client.post(f"/admin/inventario/sessoes/{sid}/itens", json={"codigo": "ABC", "nome": "Item", "grupo": "G", "familia": "F"})
        resp = client.patch(f"/admin/inventario/sessoes/{sid}/itens/ABC", json={"quantidade": 10})
        assert resp.status_code == 200
        itens = client.get(f"/admin/inventario/sessoes/{sid}/itens").json()
        assert itens[0]["quantidade"] == 10

    def test_atualizar_item_zera_e_remove(self, client):
        sessao = client.post("/admin/inventario/sessoes", json={"nome": "Teste"}).json()
        sid = sessao["id"]
        client.post(f"/admin/inventario/sessoes/{sid}/itens", json={"codigo": "ABC", "nome": "Item", "grupo": "G", "familia": "F"})
        client.patch(f"/admin/inventario/sessoes/{sid}/itens/ABC", json={"quantidade": 0})
        itens = client.get(f"/admin/inventario/sessoes/{sid}/itens").json()
        assert len(itens) == 0

    def test_limpar_itens(self, client):
        sessao = client.post("/admin/inventario/sessoes", json={"nome": "Teste"}).json()
        sid = sessao["id"]
        client.post(f"/admin/inventario/sessoes/{sid}/itens", json={"codigo": "A", "nome": "X", "grupo": "G", "familia": "F"})
        client.post(f"/admin/inventario/sessoes/{sid}/itens", json={"codigo": "B", "nome": "Y", "grupo": "G", "familia": "F"})
        resp = client.delete(f"/admin/inventario/sessoes/{sid}/itens")
        assert resp.status_code == 200
        itens = client.get(f"/admin/inventario/sessoes/{sid}/itens").json()
        assert len(itens) == 0

    def test_encerrar_sessao(self, client):
        sessao = client.post("/admin/inventario/sessoes", json={"nome": "Teste"}).json()
        resp = client.patch(f"/admin/inventario/sessoes/{sessao['id']}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "encerrada"

    def test_sessao_encerrada_nao_lista(self, client):
        sessao = client.post("/admin/inventario/sessoes", json={"nome": "Teste"}).json()
        client.patch(f"/admin/inventario/sessoes/{sessao['id']}")
        sessoes = client.get("/admin/inventario/sessoes").json()
        assert len(sessoes) == 0

    def test_consolidado_multi_usuario(self, client, app, db_session, usuario_admin, usuario_operador):
        """Testa que o consolidado soma itens de usuarios diferentes."""
        sessao = client.post("/admin/inventario/sessoes", json={"nome": "Consolidado"}).json()
        sid = sessao["id"]

        client.post(f"/admin/inventario/sessoes/{sid}/itens", json={"codigo": "ABC", "nome": "Item", "grupo": "G", "familia": "F", "quantidade": 2})

        from app.domain.models.inventario import ItemInventario as ItemInventarioModel
        item_oper = ItemInventarioModel(sessao_id=sid, usuario_id=usuario_operador.id, codigo="ABC", nome="Item", grupo="G", familia="F", quantidade=3)
        db_session.add(item_oper)
        db_session.commit()

        itens_admin = client.get(f"/admin/inventario/sessoes/{sid}/itens?consolidado=true").json()
        assert len(itens_admin) == 1
        assert itens_admin[0]["quantidade"] == 5

        itens_admin_proprios = client.get(f"/admin/inventario/sessoes/{sid}/itens").json()
        assert len(itens_admin_proprios) == 1
        assert itens_admin_proprios[0]["quantidade"] == 2
