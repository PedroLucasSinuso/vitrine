import os

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.domain.models.empresa import Empresa
from app.infrastructure.db.database import Base


def _engine_sqlite_com_fk():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _ligar_fk(conexao, _):
        conexao.execute("PRAGMA foreign_keys=ON")

    return engine


def engine_de_teste(nome: str):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(_banco_isolado(url, nome))


def _banco_isolado(url: str, nome: str) -> str:
    base = make_url(url)
    banco = f"{base.database}_{nome}"
    admin = create_engine(base, isolation_level="AUTOCOMMIT")
    with admin.connect() as conexao:
        conexao.execute(text(f'DROP DATABASE IF EXISTS "{banco}" WITH (FORCE)'))
        conexao.execute(text(f'CREATE DATABASE "{banco}"'))
    admin.dispose()
    return base.set(database=banco).render_as_string(hide_password=False)


def _engine_postgres():
    return create_engine(os.environ["TEST_DATABASE_URL"])


BANCOS = [
    pytest.param(_engine_sqlite_com_fk, id="sqlite-fk"),
    pytest.param(
        _engine_postgres,
        id="postgres",
        marks=pytest.mark.skipif(
            not os.environ.get("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL não definida"
        ),
    ),
]


def sessao_em_banco_limpo(criar_engine, empresas: dict[int, str]):
    engine = criar_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    sessao = sessionmaker(bind=engine, autoflush=False)()
    sessao.add_all([
        Empresa(id=empresa_id, nome=slug, slug=slug, status="ativa")
        for empresa_id, slug in empresas.items()
    ])
    sessao.commit()
    try:
        yield sessao
    finally:
        sessao.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
