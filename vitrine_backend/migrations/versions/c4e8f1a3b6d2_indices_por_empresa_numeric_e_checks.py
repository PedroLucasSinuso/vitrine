"""índices compostos por empresa; Numeric para preço e CHECK de status no Postgres

Revision ID: c4e8f1a3b6d2
Revises: b7c1e4d2a9f0
Create Date: 2026-09-26 12:00:00

Tipos e CHECK só mudam no Postgres: no SQLite exigiriam recriar as tabelas.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e8f1a3b6d2"
down_revision: Union[str, None] = "b7c1e4d2a9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDICES_ANTIGOS = [
    ("ix_produtos_nome", "produtos", ["nome"]),
    ("ix_produtos_grupo", "produtos", ["grupo"]),
    ("ix_produtos_familia", "produtos", ["familia"]),
    ("ix_produto_codigos_codigo", "produto_codigos", ["codigo"]),
    ("ix_produto_codigos_codigo_chamada", "produto_codigos", ["codigo_chamada"]),
    ("ix_produto_codigos_empresa_id", "produto_codigos", ["empresa_id"]),
    ("ix_historico_precos_codigo_chamada", "historico_precos", ["codigo_chamada"]),
    ("ix_historico_precos_data_coleta", "historico_precos", ["data_coleta"]),
    ("ix_historico_precos_empresa_id", "historico_precos", ["empresa_id"]),
    ("ix_cache_status_empresa_id", "cache_status", ["empresa_id"]),
    ("ix_tentativas_login_username", "tentativas_login", ["username"]),
]

INDICES_NOVOS = [
    ("ix_produtos_empresa_nome", "produtos", ["empresa_id", "nome"]),
    ("ix_produtos_empresa_grupo", "produtos", ["empresa_id", "grupo"]),
    ("ix_produtos_empresa_familia", "produtos", ["empresa_id", "familia"]),
    ("ix_produto_codigos_empresa_codigo", "produto_codigos", ["empresa_id", "codigo"]),
    ("ix_produto_codigos_empresa_codigo_chamada", "produto_codigos", ["empresa_id", "codigo_chamada"]),
    ("ix_historico_precos_empresa_codigo_data", "historico_precos", ["empresa_id", "codigo_chamada", "data_coleta"]),
    ("ix_cache_status_empresa_last_updated", "cache_status", ["empresa_id", "last_updated"]),
    ("ix_tentativas_login_username_attempted_at", "tentativas_login", ["username", "attempted_at"]),
]

COLUNAS_PRECO = [
    ("produtos", "preco_venda"),
    ("produtos", "preco_custo"),
    ("historico_precos", "preco_venda"),
    ("historico_precos", "preco_custo"),
]

CHECKS = [
    ("ck_usuarios_role", "usuarios", "role IN ('operador', 'supervisor', 'admin', 'super_admin')"),
    ("ck_empresas_status", "empresas", "status IN ('ativa', 'suspensa')"),
    ("ck_sync_jobs_status", "sync_jobs", "status IN ('pendente', 'em_progresso', 'sucesso', 'erro')"),
    ("ck_sessoes_inventario_status", "sessoes_inventario", "status IN ('ativa', 'encerrada')"),
    ("ck_cache_status_status", "cache_status", "status IN ('sucesso', 'erro')"),
]


def _eh_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    for nome, tabela, colunas in INDICES_NOVOS:
        op.create_index(nome, tabela, colunas)
    for nome, tabela, _ in INDICES_ANTIGOS:
        op.drop_index(nome, table_name=tabela)

    if not _eh_postgres():
        return
    for tabela, coluna in COLUNAS_PRECO:
        op.alter_column(tabela, coluna, type_=sa.Numeric(14, 4), postgresql_using=f"{coluna}::numeric(14,4)")
    for nome, tabela, condicao in CHECKS:
        op.create_check_constraint(nome, tabela, condicao)


def downgrade() -> None:
    if _eh_postgres():
        for nome, tabela, _ in CHECKS:
            op.drop_constraint(nome, tabela, type_="check")
        for tabela, coluna in COLUNAS_PRECO:
            op.alter_column(tabela, coluna, type_=sa.Float())

    for nome, tabela, colunas in INDICES_ANTIGOS:
        op.create_index(nome, tabela, colunas)
    for nome, tabela, _ in INDICES_NOVOS:
        op.drop_index(nome, table_name=tabela)
