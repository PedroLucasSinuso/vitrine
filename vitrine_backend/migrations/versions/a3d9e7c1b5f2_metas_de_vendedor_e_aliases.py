"""metas de vendedor e aliases

Revision ID: a3d9e7c1b5f2
Revises: f1c6a2e9d4b8
Create Date: 2026-09-26 02:33:11.335084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3d9e7c1b5f2'
down_revision: Union[str, None] = 'f1c6a2e9d4b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('vendedores_alias',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('nome_origem', sa.String(), nullable=False),
    sa.Column('vendedor', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('empresa_id', 'nome_origem', name='uq_vendedores_alias_empresa_nome')
    )
    op.create_table('metas_vendedor',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('vendedor', sa.String(), nullable=False),
    sa.Column('competencia', sa.String(length=7), nullable=False),
    sa.Column('valor_meta', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('percentual_comissao', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('atualizado_por', sa.Integer(), nullable=True),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['atualizado_por'], ['usuarios.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('empresa_id', 'vendedor', 'competencia', name='uq_metas_empresa_vendedor_competencia')
    )


def downgrade() -> None:
    op.drop_table('metas_vendedor')
    op.drop_table('vendedores_alias')
