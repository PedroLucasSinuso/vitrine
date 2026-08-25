"""Ambiente do Alembic para o Vitrine backend.

A URL de conexão vem de app.core.config.settings (a mesma fonte que o resto
da aplicação usa), não de alembic.ini — assim um único .env continua sendo a
verdade sobre onde o banco está, em dev, Docker ou produção.

Para SQLite, ``render_as_batch=True`` é obrigatório: o SQLite não suporta
ALTER TABLE completo (ex: alterar tipo/remover coluna), então o Alembic
recria a tabela nos bastidores quando necessário (batch mode).
"""

import pkgutil
import importlib
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.infrastructure.db.database import Base

# Auto-scan de models — mesmo padrão usado em app/infrastructure/db/bootstrap.py,
# necessário para que Base.metadata conheça todas as tabelas antes do autogenerate.
import app.domain.models as _models_pkg
for _module_info in pkgutil.iter_modules(_models_pkg.__path__):
    importlib.import_module(f"app.domain.models.{_module_info.name}")

config = context.config

if config.config_file_name is not None:
    # disable_existing_loggers=False e obrigatorio aqui: o padrao do
    # fileConfig e True, e como init_db() roda `alembic upgrade head` no
    # startup da aplicacao, ele desligaria todo logger `app.*` ja
    # importado — o processo inteiro pararia de logar depois da migracao.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata

# Sobrescreve a URL do alembic.ini com a URL real da aplicação.
config.set_main_option("sqlalchemy.url", settings.sqlite_url)


def _is_sqlite() -> bool:
    return settings.sqlite_url.startswith("sqlite")


def run_migrations_offline() -> None:
    """Gera SQL sem se conectar ao banco (``alembic upgrade --sql``)."""
    context.configure(
        url=settings.sqlite_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=_is_sqlite(),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migrações conectando de fato ao banco (uso normal)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=_is_sqlite(),
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
