"""segmento equipe

Revision ID: c7a1d5e3f9b2
Revises: b8e2f4a6c9d1
Create Date: 2026-09-26 18:00:00
"""
from typing import Sequence, Union

from alembic import op


revision: str = "c7a1d5e3f9b2"
down_revision: Union[str, None] = "b8e2f4a6c9d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _eh_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def _recriar(valores: str) -> None:
    op.drop_constraint("ck_empresas_segmento", "empresas", type_="check")
    op.create_check_constraint("ck_empresas_segmento", "empresas", f"segmento IN ({valores})")


def upgrade() -> None:
    if _eh_postgres():
        _recriar("'supermercado', 'moda', 'varejo', 'equipe'")


def downgrade() -> None:
    if _eh_postgres():
        _recriar("'supermercado', 'moda', 'varejo'")
