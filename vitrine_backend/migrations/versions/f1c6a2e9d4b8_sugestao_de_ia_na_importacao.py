"""sugestao de ia na importacao

Revision ID: f1c6a2e9d4b8
Revises: e5b3d8f2a1c7
Create Date: 2026-09-26 02:25:46.379610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f1c6a2e9d4b8'
down_revision: Union[str, None] = 'e5b3d8f2a1c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('arquivos_importados', sa.Column('sugestao_ia', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True))
    op.add_column('arquivos_importados', sa.Column('ia_usada', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('arquivos_importados') as batch_op:
        batch_op.drop_column('ia_usada')
        batch_op.drop_column('sugestao_ia')
