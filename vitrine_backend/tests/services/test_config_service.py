"""Testes do ConfigService (app.application.config_service)."""

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.domain.models.configuracao import Configuracao
from app.infrastructure.db.database import Base
from app.application.config_service import (
    get,
    set_many,
    invalidar_cache,
    is_sensitive,
    CHAVES_EDITAVEIS,
    _get_env_fallback,
    _cache,
    SENTINEL_MASCARADO,
)


# ── Engine e sessão compartilhados ─────────────────────────────────────────

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Cria uma sessão limpa para cada teste."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def cleanup():
    """Limpa tabela e cache entre testes."""
    yield
    with SessionLocal.begin() as sess:
        sess.execute(Configuracao.__table__.delete())
    _cache.clear()


# ── is_sensitive ───────────────────────────────────────────────────────────


class TestIsSensitive:
    def test_chave_explicita(self):
        assert is_sensitive("twilio_auth_token") is True
        assert is_sensitive("smtp_password") is True
        assert is_sensitive("anthropic_api_key") is True
        assert is_sensitive("erp_postgres_url") is True

    def test_chave_por_padrao_regex(self):
        assert is_sensitive("my_secret_key") is True
        assert is_sensitive("api_token_foo") is True
        assert is_sensitive("other_password") is True

    def test_chave_nao_sensivel(self):
        assert is_sensitive("nome_estabelecimento") is False
        assert is_sensitive("report_day") is False
        assert is_sensitive("cache_refresh_interval") is False
        assert is_sensitive("twilio_from_number") is False


# ── get ────────────────────────────────────────────────────────────────────


class TestGet:
    def test_retorna_valor_do_banco(self, db):
        db.add(Configuracao(chave="nome_estabelecimento", valor="Minha Loja"))
        db.commit()
        assert get(db, "nome_estabelecimento") == "Minha Loja"

    def test_retorna_default_quando_nao_existe(self, db):
        assert get(db, "chave_inexistente", "padrao") == "padrao"

    def test_retorna_vazio_quando_sem_default(self, db):
        assert get(db, "chave_inexistente") == ""

    def test_cache_funciona(self, db):
        db.add(Configuracao(chave="foo", valor="original"))
        db.commit()
        assert get(db, "foo") == "original"

        # Muda no banco diretamente (sem invalidar cache)
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == "foo")
        ).scalar_one()
        row.valor = "alterado"
        db.commit()

        # Cache ainda retorna o valor antigo (TTL de 30s)
        assert get(db, "foo") == "original"

    def test_cache_ignorado_apos_invalidar(self, db):
        db.add(Configuracao(chave="foo", valor="original"))
        db.commit()
        assert get(db, "foo") == "original"

        invalidar_cache()

        row = db.execute(
            select(Configuracao).where(Configuracao.chave == "foo")
        ).scalar_one()
        row.valor = "alterado"
        db.commit()

        assert get(db, "foo") == "alterado"


# ── set_many ───────────────────────────────────────────────────────────────


class TestSetMany:
    def test_salva_novas_configs(self, db):
        set_many(db, {"nome_estabelecimento": "Loja Teste"})
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == "nome_estabelecimento")
        ).scalar_one()
        assert row.valor == "Loja Teste"

    def test_atualiza_config_existente(self, db):
        db.add(Configuracao(chave="nome_estabelecimento", valor="Antigo"))
        db.commit()

        set_many(db, {"nome_estabelecimento": "Novo"})
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == "nome_estabelecimento")
        ).scalar_one()
        assert row.valor == "Novo"

    def test_rejeita_chave_nao_editavel(self, db):
        set_many(db, {"jwt_secret": "hack123"})
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == "jwt_secret")
        ).scalar_one_or_none()
        assert row is None

    def test_mistura_chaves_validas_e_invalidas(self, db):
        set_many(db, {
            "nome_estabelecimento": "Loja",
            "jwt_secret": "hack123",
            "smtp_host": "smtp.teste.com",
        })
        assert get(db, "nome_estabelecimento") == "Loja"
        assert get(db, "smtp_host") == "smtp.teste.com"
        assert get(db, "jwt_secret") == ""

    def test_invalida_cache_ao_salvar(self, db):
        set_many(db, {"nome_estabelecimento": "Primeiro"})
        assert get(db, "nome_estabelecimento") == "Primeiro"

        set_many(db, {"nome_estabelecimento": "Segundo"})
        assert get(db, "nome_estabelecimento") == "Segundo"

    def test_sentinel_preserva_valor_existente(self, db):
        db.add(Configuracao(chave="nome_estabelecimento", valor="Minha Loja"))
        db.commit()

        set_many(db, {"nome_estabelecimento": SENTINEL_MASCARADO})
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == "nome_estabelecimento")
        ).scalar_one()
        assert row.valor == "Minha Loja"

    def test_sentinel_em_chave_inexistente_salva_literal(self, db):
        """Se a chave não existe, o sentinel é salvo como valor literal."""
        set_many(db, {"chave_teste": SENTINEL_MASCARADO})
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == "chave_teste")
        ).scalar_one_or_none()
        assert row is None  # chave_teste não está em CHAVES_EDITAVEIS

    def test_sentinel_em_chave_editavel_inexistente_salva_literal(self, db):
        """Chave editável que não existe: sentinel vira valor literal."""
        set_many(db, {"logo_url": SENTINEL_MASCARADO})
        row = db.execute(
            select(Configuracao).where(Configuracao.chave == "logo_url")
        ).scalar_one()
        assert row.valor == SENTINEL_MASCARADO


# ── is_sensitive + CHAVES_EDITAVEIS consistency ────────────────────────────


class TestConsistency:
    def test_chaves_sensiveis_tb_sao_editaveis(self):
        """Toda chave sensível deve estar na whitelist para poder ser configurada."""
        sensiveis_editaveis = [
            "twilio_auth_token",
            "twilio_account_sid",
            "smtp_password",
            "anthropic_api_key",
            "erp_postgres_url",
        ]
        for chave in sensiveis_editaveis:
            assert chave in CHAVES_EDITAVEIS, (
                f"{chave} é sensível mas não está em CHAVES_EDITAVEIS"
            )

    def test_chaves_fallback_estao_em_chaves_editaveis(self):
        """Toda chave com fallback .env deve estar na whitelist."""
        chaves_fallback = [
            "erp_postgres_url",
            "twilio_account_sid",
            "twilio_auth_token",
            "twilio_from_number",
            "smtp_host",
            "smtp_port",
            "smtp_user",
            "smtp_password",
            "email_from",
            "cache_refresh_interval",
        ]
        for chave in chaves_fallback:
            assert chave in CHAVES_EDITAVEIS, (
                f"{chave} tem fallback .env mas não está em CHAVES_EDITAVEIS"
            )


# ── _get_env_fallback ──────────────────────────────────────────────────────


class TestEnvFallback:
    def test_chave_sem_fallback_retorna_none(self):
        assert _get_env_fallback("nome_estabelecimento") is None

    def test_chave_com_fallback_mas_settings_vazio(self):
        val = _get_env_fallback("anthropic_api_key")
        assert val is None
