"""multi-tenant: empresa_id em todos os models operacionais

Revision ID: a5fd05b616fd
Revises: fc9067718964
Create Date: 2026-08-23 17:15:21.519114

Escrita à mão a partir do diff do autogenerate: o autogenerate não detecta
mudança de PRIMARY KEY (produtos e configuracoes ganham PK composta) nem
sabe que bancos existentes têm dados a preservar.

Estratégia por grupo de tabela:

  - 'produtos', 'produto_codigos', 'historico_precos', 'configuracoes'
    (mudam de chave primária/FK): SQLite não nomeia constraints implícitas
    (PK/FK declaradas sem `name=`), e o modo batch do Alembic exige um
    nome para dropar uma constraint — como as originais são todas
    anônimas, isso é impossível via drop_constraint(). Solução: recriação
    manual da tabela (o "12-step ALTER TABLE" recomendado pela própria
    documentação do SQLite) — cria a tabela nova, copia os dados,
    descarta a antiga, renomeia.
  - Todas as outras tabelas (só GANHAM uma coluna/índice/FK nova, sem
    remover nada): batch_alter_table normal, mais simples.

Todo dado pré-existente pertence, por definição, à empresa padrão (id=1)
semeada no início desta migração — o app era single-tenant até agora.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a5fd05b616fd'
down_revision: Union[str, None] = 'fc9067718964'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_EMPRESA_ID = 1

_TABELAS_SIMPLES = [
    "cache_status",
    "email_contatos",
    "grupos_familias",
    "itens_inventario",
    "sessoes_inventario",
    "sync_jobs",
    "whatsapp_contatos",
]


def upgrade() -> None:
    # ── 1. empresas + tenant padrão ─────────────────────────────────────
    op.create_table(
        "empresas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("empresas", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_empresas_slug"), ["slug"], unique=True)

    op.execute(
        "INSERT INTO empresas (id, nome, slug, status, criado_em) "
        "VALUES (1, 'Empresa Padrão', 'default', 'ativa', CURRENT_TIMESTAMP)"
    )

    # ── 2. usuarios: empresa_id NULLABLE (super_admin não tem tenant) ──
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.add_column(sa.Column("empresa_id", sa.Integer(), nullable=True))
    op.execute(f"UPDATE usuarios SET empresa_id = {DEFAULT_EMPRESA_ID}")
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_usuarios_empresa_id"), ["empresa_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_usuarios_empresa_id_empresas", "empresas", ["empresa_id"], ["id"], ondelete="CASCADE"
        )

    # ── 3. tabelas simples: só ganham coluna/índice/FK — batch normal ──
    for tabela in _TABELAS_SIMPLES:
        with op.batch_alter_table(tabela, schema=None) as batch_op:
            batch_op.add_column(sa.Column("empresa_id", sa.Integer(), nullable=True))
        op.execute(f"UPDATE {tabela} SET empresa_id = {DEFAULT_EMPRESA_ID}")
        with op.batch_alter_table(tabela, schema=None) as batch_op:
            batch_op.alter_column("empresa_id", nullable=False)
            batch_op.create_index(batch_op.f(f"ix_{tabela}_empresa_id"), ["empresa_id"], unique=False)
            batch_op.create_foreign_key(
                f"fk_{tabela}_empresa_id_empresas", "empresas", ["empresa_id"], ["id"], ondelete="CASCADE"
            )

    # ── 4. produtos / produto_codigos / historico_precos / configuracoes:
    #        recriação manual (constraints originais são anônimas) ──────
    op.execute("PRAGMA foreign_keys=OFF")

    # -- produtos: PK vira (empresa_id, codigo_chamada) --
    op.execute(f"""
        CREATE TABLE produtos_new (
            empresa_id INTEGER NOT NULL,
            codigo_chamada VARCHAR NOT NULL,
            nome VARCHAR NOT NULL,
            grupo VARCHAR NOT NULL,
            familia VARCHAR NOT NULL,
            preco_venda FLOAT NOT NULL,
            preco_custo FLOAT NOT NULL,
            estoque FLOAT NOT NULL,
            ativo BOOLEAN NOT NULL DEFAULT 1,
            PRIMARY KEY (empresa_id, codigo_chamada),
            FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
        )
    """)
    op.execute(f"""
        INSERT INTO produtos_new (empresa_id, codigo_chamada, nome, grupo, familia,
                                   preco_venda, preco_custo, estoque, ativo)
        SELECT {DEFAULT_EMPRESA_ID}, codigo_chamada, nome, grupo, familia,
               preco_venda, preco_custo, estoque, ativo
        FROM produtos
    """)
    op.execute("DROP TABLE produtos")
    op.execute("ALTER TABLE produtos_new RENAME TO produtos")
    op.create_index("ix_produtos_nome", "produtos", ["nome"])
    op.create_index("ix_produtos_grupo", "produtos", ["grupo"])
    op.create_index("ix_produtos_familia", "produtos", ["familia"])

    # -- produto_codigos: empresa_id + FK composta p/ produtos --
    op.execute(f"""
        CREATE TABLE produto_codigos_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            codigo VARCHAR NOT NULL,
            codigo_chamada VARCHAR NOT NULL,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
            FOREIGN KEY (empresa_id, codigo_chamada) REFERENCES produtos(empresa_id, codigo_chamada) ON DELETE CASCADE
        )
    """)
    op.execute(f"""
        INSERT INTO produto_codigos_new (id, empresa_id, codigo, codigo_chamada)
        SELECT id, {DEFAULT_EMPRESA_ID}, codigo, codigo_chamada
        FROM produto_codigos
    """)
    op.execute("DROP TABLE produto_codigos")
    op.execute("ALTER TABLE produto_codigos_new RENAME TO produto_codigos")
    op.create_index("ix_produto_codigos_codigo", "produto_codigos", ["codigo"])
    op.create_index("ix_produto_codigos_codigo_chamada", "produto_codigos", ["codigo_chamada"])
    op.create_index("ix_produto_codigos_empresa_id", "produto_codigos", ["empresa_id"])

    # -- historico_precos: empresa_id + FK composta p/ produtos --
    op.execute(f"""
        CREATE TABLE historico_precos_new (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            codigo_chamada VARCHAR NOT NULL,
            preco_custo FLOAT NOT NULL,
            preco_venda FLOAT NOT NULL,
            markup FLOAT NOT NULL,
            margem FLOAT NOT NULL,
            data_coleta DATETIME NOT NULL,
            sync_job_id INTEGER,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
            FOREIGN KEY (empresa_id, codigo_chamada) REFERENCES produtos(empresa_id, codigo_chamada) ON DELETE CASCADE,
            FOREIGN KEY (sync_job_id) REFERENCES sync_jobs(id) ON DELETE SET NULL
        )
    """)
    op.execute(f"""
        INSERT INTO historico_precos_new (id, empresa_id, codigo_chamada, preco_custo, preco_venda,
                                           markup, margem, data_coleta, sync_job_id)
        SELECT id, {DEFAULT_EMPRESA_ID}, codigo_chamada, preco_custo, preco_venda,
               markup, margem, data_coleta, sync_job_id
        FROM historico_precos
    """)
    op.execute("DROP TABLE historico_precos")
    op.execute("ALTER TABLE historico_precos_new RENAME TO historico_precos")
    op.create_index("ix_historico_precos_codigo_chamada", "historico_precos", ["codigo_chamada"])
    op.create_index("ix_historico_precos_data_coleta", "historico_precos", ["data_coleta"])
    op.create_index("ix_historico_precos_empresa_id", "historico_precos", ["empresa_id"])

    # -- configuracoes: PK vira (empresa_id, chave) --
    op.execute(f"""
        CREATE TABLE configuracoes_new (
            empresa_id INTEGER NOT NULL,
            chave VARCHAR NOT NULL,
            valor VARCHAR NOT NULL,
            atualizado_em DATETIME NOT NULL,
            PRIMARY KEY (empresa_id, chave),
            FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
        )
    """)
    op.execute(f"""
        INSERT INTO configuracoes_new (empresa_id, chave, valor, atualizado_em)
        SELECT {DEFAULT_EMPRESA_ID}, chave, valor, atualizado_em
        FROM configuracoes
    """)
    op.execute("DROP TABLE configuracoes")
    op.execute("ALTER TABLE configuracoes_new RENAME TO configuracoes")

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    op.execute("""
        CREATE TABLE configuracoes_old (
            chave VARCHAR NOT NULL PRIMARY KEY,
            valor VARCHAR NOT NULL,
            atualizado_em DATETIME
        )
    """)
    op.execute(f"INSERT INTO configuracoes_old SELECT chave, valor, atualizado_em FROM configuracoes WHERE empresa_id = {DEFAULT_EMPRESA_ID}")
    op.execute("DROP TABLE configuracoes")
    op.execute("ALTER TABLE configuracoes_old RENAME TO configuracoes")

    op.execute("""
        CREATE TABLE historico_precos_old (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            codigo_chamada VARCHAR,
            preco_custo FLOAT NOT NULL,
            preco_venda FLOAT NOT NULL,
            markup FLOAT NOT NULL,
            margem FLOAT NOT NULL,
            data_coleta DATETIME NOT NULL,
            sync_job_id INTEGER,
            FOREIGN KEY (codigo_chamada) REFERENCES produtos(codigo_chamada) ON DELETE CASCADE,
            FOREIGN KEY (sync_job_id) REFERENCES sync_jobs(id) ON DELETE SET NULL
        )
    """)
    op.execute("INSERT INTO historico_precos_old SELECT id, codigo_chamada, preco_custo, preco_venda, markup, margem, data_coleta, sync_job_id FROM historico_precos")
    op.execute("DROP TABLE historico_precos")
    op.execute("ALTER TABLE historico_precos_old RENAME TO historico_precos")
    op.create_index("ix_historico_precos_codigo_chamada", "historico_precos", ["codigo_chamada"])
    op.create_index("ix_historico_precos_data_coleta", "historico_precos", ["data_coleta"])

    op.execute("""
        CREATE TABLE produto_codigos_old (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            codigo VARCHAR,
            codigo_chamada VARCHAR NOT NULL,
            FOREIGN KEY (codigo_chamada) REFERENCES produtos(codigo_chamada) ON DELETE CASCADE
        )
    """)
    op.execute("INSERT INTO produto_codigos_old SELECT id, codigo, codigo_chamada FROM produto_codigos")
    op.execute("DROP TABLE produto_codigos")
    op.execute("ALTER TABLE produto_codigos_old RENAME TO produto_codigos")
    op.create_index("ix_produto_codigos_codigo", "produto_codigos", ["codigo"])
    op.create_index("ix_produto_codigos_codigo_chamada", "produto_codigos", ["codigo_chamada"])

    op.execute("""
        CREATE TABLE produtos_old (
            codigo_chamada VARCHAR NOT NULL PRIMARY KEY,
            nome VARCHAR,
            grupo VARCHAR,
            familia VARCHAR,
            preco_venda FLOAT,
            preco_custo FLOAT,
            estoque FLOAT,
            ativo BOOLEAN NOT NULL DEFAULT 1
        )
    """)
    op.execute(f"INSERT INTO produtos_old SELECT codigo_chamada, nome, grupo, familia, preco_venda, preco_custo, estoque, ativo FROM produtos WHERE empresa_id = {DEFAULT_EMPRESA_ID}")
    op.execute("DROP TABLE produtos")
    op.execute("ALTER TABLE produtos_old RENAME TO produtos")
    op.create_index("ix_produtos_nome", "produtos", ["nome"])
    op.create_index("ix_produtos_grupo", "produtos", ["grupo"])
    op.create_index("ix_produtos_familia", "produtos", ["familia"])

    op.execute("PRAGMA foreign_keys=ON")

    for tabela in reversed(_TABELAS_SIMPLES):
        with op.batch_alter_table(tabela, schema=None) as batch_op:
            batch_op.drop_constraint(f"fk_{tabela}_empresa_id_empresas", type_="foreignkey")
            batch_op.drop_index(batch_op.f(f"ix_{tabela}_empresa_id"))
            batch_op.drop_column("empresa_id")

    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.drop_constraint("fk_usuarios_empresa_id_empresas", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_usuarios_empresa_id"))
        batch_op.drop_column("empresa_id")

    with op.batch_alter_table("empresas", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_empresas_slug"))
    op.drop_table("empresas")
