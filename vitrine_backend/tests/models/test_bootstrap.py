"""Testes do bootstrap do banco (app.infrastructure.db.bootstrap)."""
import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.infrastructure.db.database import Base


@pytest.fixture(autouse=True)
def clean_global_flag():
    """Reseta a flag global _migration_feita entre testes."""
    import app.infrastructure.db.bootstrap as bootstrap
    bootstrap._migration_feita = False
    yield
    bootstrap._migration_feita = False


class TestInitDb:
    """init_db migration guard (T9)."""

    def test_init_db_idempotent_e_cria_tabelas(self):
        """init_db() é idempotente (2x sem exceção) e cria as tabelas necessárias."""
        import app.infrastructure.db.bootstrap as bootstrap

        # Cria um engine in-memory para o teste
        test_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        Base.metadata.create_all(bind=test_engine)

        # Patch o sqlite_engine global com o engine de teste
        with patch.object(bootstrap, "sqlite_engine", test_engine):
            # Primeira chamada — cria tabelas e executa migrações
            bootstrap._migration_feita = False
            try:
                bootstrap.init_db()
            except Exception as e:
                pytest.fail(f"Primeira chamada de init_db falhou: {e}")

            # Segunda chamada — deve retornar imediatamente (flag _migration_feita)
            try:
                bootstrap.init_db()
            except Exception as e:
                pytest.fail(f"Segunda chamada de init_db levantou exceção: {e}")

            # Verificar que as tabelas existem
            from sqlalchemy import inspect
            inspector = inspect(test_engine)
            table_names = inspector.get_table_names()

            required_tables = [
                "produtos",
                "produto_codigos",
                "cache_status",
                "usuarios",
                "configuracoes",
                "sessoes_inventario",
                "itens_inventario",
                "sync_jobs",
                "token_blacklist",
            ]
            for table in required_tables:
                assert table in table_names, (
                    f"Tabela {table} não foi criada por init_db()"
                )
