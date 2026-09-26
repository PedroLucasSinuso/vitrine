"""segmento e modo de operação da empresa

Revision ID: d2a7c9e1f4b3
Revises: c4e8f1a3b6d2
Create Date: 2026-09-26 14:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2a7c9e1f4b3"
down_revision: Union[str, None] = "c4e8f1a3b6d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _eh_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    op.add_column("empresas", sa.Column("segmento", sa.String(), nullable=False, server_default="supermercado"))
    op.add_column("empresas", sa.Column("modo", sa.String(), nullable=False, server_default="legado"))
    if _eh_postgres():
        op.create_check_constraint(
            "ck_empresas_segmento", "empresas", "segmento IN ('supermercado', 'moda', 'varejo')"
        )
        op.create_check_constraint("ck_empresas_modo", "empresas", "modo IN ('legado', 'upload', 'agente')")


def downgrade() -> None:
    if _eh_postgres():
        op.drop_constraint("ck_empresas_modo", "empresas", type_="check")
        op.drop_constraint("ck_empresas_segmento", "empresas", type_="check")
        op.drop_column("empresas", "modo")
        op.drop_column("empresas", "segmento")
        return
    with op.batch_alter_table("empresas") as batch_op:
        batch_op.drop_column("modo")
        batch_op.drop_column("segmento")
