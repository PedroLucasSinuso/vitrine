import os
os.environ["RATE_LIMIT_ENABLED"] = "0"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db
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
def usuario_operador(db_session):
    user = Usuario(
        username="operador1",
        nome_exibicao="Operador Um",
        role="operador",
        hashed_password=hash_password("senha123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def usuario_supervisor(db_session):
    user = Usuario(
        username="supervisor1",
        nome_exibicao="Supervisor Um",
        role="supervisor",
        hashed_password=hash_password("senha123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def usuario_admin(db_session):
    user = Usuario(
        username="admin1",
        nome_exibicao="Admin Um",
        role="admin",
        hashed_password=hash_password("senha123"),
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