import os
os.environ["RATE_LIMIT_ENABLED"] = "0"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from datetime import date, time
from decimal import Decimal

from app.main import app
from app.api.deps import get_db, get_transaction_source
from app.infrastructure.db.database import Base
from app.application.utils.security import hash_password
from app.core.models.transaction import TransactionItem, OperationType
from app.domain.models.usuario import Usuario
from app.domain.models.empresa import Empresa


SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="function")
def db_session(reset_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def empresa_padrao(db_session):
    """Empresa (tenant) padrão usada por todos os fixtures de usuário —
    sem isso, Usuario.empresa_id fica None (reservado para super_admin) e
    todo o código escopado por tenant (repositórios, config_service, ...)
    não encontra nada."""
    empresa = Empresa(nome="Empresa Teste", slug="empresa-teste", status="ativa")
    db_session.add(empresa)
    db_session.commit()
    db_session.refresh(empresa)
    return empresa


@pytest.fixture
def usuario_operador(db_session, empresa_padrao):
    user = Usuario(
        username="operador1",
        nome_exibicao="Operador Um",
        role="operador",
        hashed_password=hash_password("senha123"),
        token_version=0,
        empresa_id=empresa_padrao.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def usuario_supervisor(db_session, empresa_padrao):
    user = Usuario(
        username="supervisor1",
        nome_exibicao="Supervisor Um",
        role="supervisor",
        hashed_password=hash_password("senha123"),
        token_version=0,
        empresa_id=empresa_padrao.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def usuario_admin(db_session, empresa_padrao):
    user = Usuario(
        username="admin1",
        nome_exibicao="Admin Um",
        role="admin",
        hashed_password=hash_password("senha123"),
        token_version=0,
        empresa_id=empresa_padrao.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_token(client: TestClient, username: str, password: str = "senha123") -> str:
    response = client.post(
        "/auth/token",
        data={"username": username, "password": password},
    )
    return response.json()["access_token"]


@pytest.fixture
def token_operador(client, usuario_operador):
    return get_token(client, "operador1")


@pytest.fixture
def token_supervisor(client, usuario_supervisor):
    return get_token(client, "supervisor1")


@pytest.fixture
def token_admin(client, usuario_admin):
    return get_token(client, "admin1")


# ── Fonte de transações falsa (BI) ───────────────────────────────────────────
#
# `get_transaction_source` é uma dependência do FastAPI: ela é resolvida
# ANTES do corpo da rota rodar. Sem substituí-la, qualquer teste que bata
# numa rota de BI tenta abrir conexão com o Postgres do ERP e morre com
# "ERP não configurado" — inclusive testes que só queriam checar validação
# de parâmetro ou permissão, que nem chegam a olhar os dados.

class FakeTransactionSource:
    """TransactionSource em memória, alimentado por um dict {data: [itens]}."""

    def __init__(self, items_por_data: dict[date, list[TransactionItem]] | None = None):
        self.items_por_data = items_por_data or {}

    def get_items(self, start: date, end: date) -> list[TransactionItem]:
        itens: list[TransactionItem] = []
        for dia, items in self.items_por_data.items():
            if start <= dia <= end:
                itens.extend(items)
        return itens

    def get_kpi_aggregates(self, start: date, end: date) -> dict | None:
        # Mesmo default da interface: força o domínio a calcular pelas linhas.
        return None


def criar_transaction_item(
    document_id: str,
    data: date,
    hora: int,
    valor: float,
    qtd: float = 1.0,
    operacao: OperationType = OperationType.SALE,
) -> TransactionItem:
    """Cria um TransactionItem de teste com os campos que o BI usa."""
    return TransactionItem(
        document_id=document_id,
        date=data,
        time=time(hora, 0),
        operation=operacao,
        line_total=Decimal(str(valor)),
        quantity=Decimal(str(qtd)),
        product_code="789001",
        product_name="Produto Teste",
        group_name="GRUPO",
        family_name="FAMILIA",
    )


@pytest.fixture
def transaction_source(client):
    """Substitui a fonte de transações por um fake vazio e devolve o fake.

    Depende de `client` de propósito: o override precisa ser instalado
    depois que o TestClient existe e some no `dependency_overrides.clear()`
    do teardown dele. Para dar dados ao teste, preencha `items_por_data`.
    """
    fake = FakeTransactionSource()
    app.dependency_overrides[get_transaction_source] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_transaction_source, None)


@pytest.fixture
def criar_item():
    """Entrega o helper de TransactionItem como fixture (evita importar
    conftest por caminho nos módulos de teste)."""
    return criar_transaction_item
