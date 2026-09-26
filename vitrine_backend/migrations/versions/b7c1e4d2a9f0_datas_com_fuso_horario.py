"""datas com fuso horário (timestamptz) no Postgres

Revision ID: b7c1e4d2a9f0
Revises: a5fd05b616fd
Create Date: 2026-09-26 10:00:00

O SQLite não guarda fuso: lá a revisão não faz nada.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c1e4d2a9f0"
down_revision: Union[str, None] = "a5fd05b616fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUNAS = [
    ("cache_status", "last_updated"),
    ("configuracoes", "atualizado_em"),
    ("empresas", "criado_em"),
    ("historico_precos", "data_coleta"),
    ("sessoes_inventario", "criado_em"),
    ("sessoes_inventario", "encerrado_em"),
    ("sync_jobs", "started_at"),
    ("sync_jobs", "finished_at"),
    ("tentativas_login", "attempted_at"),
    ("token_blacklist", "expires_at"),
    ("token_blacklist", "revoked_at"),
]


def _alterar(com_fuso: bool) -> None:
    if op.get_bind().dialect.name == "sqlite":
        return
    for tabela, coluna in COLUNAS:
        op.alter_column(
            tabela,
            coluna,
            type_=sa.DateTime(timezone=com_fuso),
            postgresql_using=f"{coluna} AT TIME ZONE 'UTC'",
        )


def upgrade() -> None:
    _alterar(com_fuso=True)


def downgrade() -> None:
    _alterar(com_fuso=False)
