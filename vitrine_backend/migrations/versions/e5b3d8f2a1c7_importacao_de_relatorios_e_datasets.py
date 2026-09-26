"""importacao de relatorios e datasets

Revision ID: e5b3d8f2a1c7
Revises: d2a7c9e1f4b3
Create Date: 2026-09-26 01:52:38.719303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e5b3d8f2a1c7'
down_revision: Union[str, None] = 'd2a7c9e1f4b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('templates_importacao',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('assinatura', sa.String(length=64), nullable=False),
    sa.Column('versao', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('mapeamento', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('erp_origem', sa.String(), nullable=True),
    sa.Column('criado_por_empresa_id', sa.Integer(), nullable=True),
    sa.Column('usos', sa.Integer(), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("tipo IN ('itens_venda', 'vendas_diarias', 'vendas_vendedor_periodo', 'vendas_produto_periodo', 'contatos_vendedor')", name='ck_templates_importacao_tipo'),
    sa.ForeignKeyConstraint(['criado_por_empresa_id'], ['empresas.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('assinatura', 'versao', name='uq_templates_assinatura_versao')
    )
    op.create_index(op.f('ix_templates_importacao_assinatura'), 'templates_importacao', ['assinatura'], unique=False)
    op.create_table('arquivos_importados',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=True),
    sa.Column('nome_original', sa.String(), nullable=False),
    sa.Column('formato', sa.String(), nullable=False),
    sa.Column('tamanho', sa.Integer(), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('caminho', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('mapeamento', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('template_id', sa.Integer(), nullable=True),
    sa.Column('erro', sa.String(), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expira_em', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('aguardando_mapeamento', 'pronto', 'divergente', 'confirmado', 'erro')", name='ck_arquivos_importados_status'),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['template_id'], ['templates_importacao.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_arquivos_importados_empresa_criado', 'arquivos_importados', ['empresa_id', 'criado_em'], unique=False)
    op.create_table('datasets',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('empresa_id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.String(), nullable=False),
    sa.Column('inicio', sa.Date(), nullable=False),
    sa.Column('fim', sa.Date(), nullable=False),
    sa.Column('linhas', sa.Integer(), nullable=False),
    sa.Column('arquivo_id', sa.Integer(), nullable=True),
    sa.Column('nome_origem', sa.String(), nullable=False),
    sa.Column('template_id', sa.Integer(), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("tipo IN ('itens_venda', 'vendas_diarias', 'vendas_vendedor_periodo', 'vendas_produto_periodo', 'contatos_vendedor')", name='ck_datasets_tipo'),
    sa.ForeignKeyConstraint(['arquivo_id'], ['arquivos_importados.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['template_id'], ['templates_importacao.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_datasets_empresa_tipo_periodo', 'datasets', ['empresa_id', 'tipo', 'inicio', 'fim'], unique=False)
    op.create_table('ds_contatos_vendedor',
    sa.Column('vendedor', sa.String(), nullable=True),
    sa.Column('contatos', sa.Integer(), nullable=False),
    sa.Column('respostas', sa.Integer(), nullable=True),
    sa.Column('conversoes', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('dataset_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ds_contatos_vendedor_dataset_id'), 'ds_contatos_vendedor', ['dataset_id'], unique=False)
    op.create_table('ds_itens_venda',
    sa.Column('documento', sa.String(), nullable=False),
    sa.Column('data', sa.Date(), nullable=False),
    sa.Column('operacao', sa.String(), nullable=False),
    sa.Column('quantidade', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('produto', sa.String(), nullable=False),
    sa.Column('codigo_produto', sa.String(), nullable=True),
    sa.Column('grupo', sa.String(), nullable=False),
    sa.Column('familia', sa.String(), nullable=False),
    sa.Column('vendedor', sa.String(), nullable=True),
    sa.Column('tamanho', sa.String(), nullable=False),
    sa.Column('cor', sa.String(), nullable=False),
    sa.Column('colecao', sa.String(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('dataset_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ds_itens_venda_dataset_id'), 'ds_itens_venda', ['dataset_id'], unique=False)
    op.create_table('ds_vendas_diarias',
    sa.Column('data', sa.Date(), nullable=False),
    sa.Column('vendedor', sa.String(), nullable=True),
    sa.Column('faturamento_bruto', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('trocas', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('atendimentos', sa.Integer(), nullable=False),
    sa.Column('pecas', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('dataset_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ds_vendas_diarias_dataset_id'), 'ds_vendas_diarias', ['dataset_id'], unique=False)
    op.create_table('ds_vendas_produto_periodo',
    sa.Column('produto', sa.String(), nullable=False),
    sa.Column('codigo_produto', sa.String(), nullable=True),
    sa.Column('grupo', sa.String(), nullable=False),
    sa.Column('familia', sa.String(), nullable=False),
    sa.Column('quantidade', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('receita', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('custo', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('dataset_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ds_vendas_produto_periodo_dataset_id'), 'ds_vendas_produto_periodo', ['dataset_id'], unique=False)
    op.create_table('ds_vendas_vendedor_periodo',
    sa.Column('vendedor', sa.String(), nullable=True),
    sa.Column('atendimentos', sa.Integer(), nullable=False),
    sa.Column('pecas', sa.Numeric(precision=14, scale=3), nullable=False),
    sa.Column('faturamento_bruto', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('trocas', sa.Numeric(precision=14, scale=2), nullable=False),
    sa.Column('faturamento_liquido', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('dataset_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ds_vendas_vendedor_periodo_dataset_id'), 'ds_vendas_vendedor_periodo', ['dataset_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ds_vendas_vendedor_periodo_dataset_id'), table_name='ds_vendas_vendedor_periodo')
    op.drop_table('ds_vendas_vendedor_periodo')
    op.drop_index(op.f('ix_ds_vendas_produto_periodo_dataset_id'), table_name='ds_vendas_produto_periodo')
    op.drop_table('ds_vendas_produto_periodo')
    op.drop_index(op.f('ix_ds_vendas_diarias_dataset_id'), table_name='ds_vendas_diarias')
    op.drop_table('ds_vendas_diarias')
    op.drop_index(op.f('ix_ds_itens_venda_dataset_id'), table_name='ds_itens_venda')
    op.drop_table('ds_itens_venda')
    op.drop_index(op.f('ix_ds_contatos_vendedor_dataset_id'), table_name='ds_contatos_vendedor')
    op.drop_table('ds_contatos_vendedor')
    op.drop_index('ix_datasets_empresa_tipo_periodo', table_name='datasets')
    op.drop_table('datasets')
    op.drop_index('ix_arquivos_importados_empresa_criado', table_name='arquivos_importados')
    op.drop_table('arquivos_importados')
    op.drop_index(op.f('ix_templates_importacao_assinatura'), table_name='templates_importacao')
    op.drop_table('templates_importacao')
