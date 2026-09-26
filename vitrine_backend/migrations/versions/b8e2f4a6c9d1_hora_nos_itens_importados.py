"""hora nos itens importados

Revision ID: b8e2f4a6c9d1
Revises: a3d9e7c1b5f2
Create Date: 2026-09-26 02:37:10.925269

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8e2f4a6c9d1'
down_revision: Union[str, None] = 'a3d9e7c1b5f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ds_itens_venda', sa.Column('hora', sa.Time(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('ds_itens_venda') as batch_op:
        batch_op.drop_column('hora')
