from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.database import Base
from vitrine_core.datasets.tipos import TipoDataset

JSONPortavel = JSON().with_variant(JSONB(), "postgresql")
DINHEIRO = Numeric(14, 2)
QUANTIDADE = Numeric(14, 3)

STATUS_ARQUIVO = ("aguardando_mapeamento", "pronto", "divergente", "confirmado", "erro")
TIPOS = tuple(t.value for t in TipoDataset)


def _em(coluna: str, valores: tuple[str, ...]) -> str:
    return "{} IN ({})".format(coluna, ", ".join(f"'{v}'" for v in valores))


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class TemplateImportacao(Base):
    __tablename__ = "templates_importacao"
    __table_args__ = (
        UniqueConstraint("assinatura", "versao", name="uq_templates_assinatura_versao"),
        CheckConstraint(_em("tipo", TIPOS), name="ck_templates_importacao_tipo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assinatura: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    mapeamento: Mapped[dict] = mapped_column(JSONPortavel, nullable=False)
    erp_origem: Mapped[str | None] = mapped_column(String, nullable=True)
    criado_por_empresa_id: Mapped[int | None] = mapped_column(
        ForeignKey("empresas.id", ondelete="SET NULL"), nullable=True
    )
    usos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_agora)


class ArquivoImportado(Base):
    __tablename__ = "arquivos_importados"
    __table_args__ = (
        Index("ix_arquivos_importados_empresa_criado", "empresa_id", "criado_em"),
        CheckConstraint(_em("status", STATUS_ARQUIVO), name="ck_arquivos_importados_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    nome_original: Mapped[str] = mapped_column(String, nullable=False)
    formato: Mapped[str] = mapped_column(String, nullable=False)
    tamanho: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    caminho: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    mapeamento: Mapped[dict | None] = mapped_column(JSONPortavel, nullable=True)
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("templates_importacao.id", ondelete="SET NULL"), nullable=True
    )
    erro: Mapped[str | None] = mapped_column(String, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_agora)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Dataset(Base):
    __tablename__ = "datasets"
    __table_args__ = (
        Index("ix_datasets_empresa_tipo_periodo", "empresa_id", "tipo", "inicio", "fim"),
        CheckConstraint(_em("tipo", TIPOS), name="ck_datasets_tipo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fim: Mapped[date] = mapped_column(Date, nullable=False)
    linhas: Mapped[int] = mapped_column(Integer, nullable=False)
    arquivo_id: Mapped[int | None] = mapped_column(
        ForeignKey("arquivos_importados.id", ondelete="SET NULL"), nullable=True
    )
    nome_origem: Mapped[str] = mapped_column(String, nullable=False)
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("templates_importacao.id", ondelete="SET NULL"), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_agora)


class _LinhaDataset:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )


class DsVendaVendedorPeriodo(_LinhaDataset, Base):
    __tablename__ = "ds_vendas_vendedor_periodo"

    vendedor: Mapped[str | None] = mapped_column(String, nullable=True)
    atendimentos: Mapped[int] = mapped_column(Integer, nullable=False)
    pecas: Mapped[Decimal] = mapped_column(QUANTIDADE, nullable=False)
    faturamento_bruto: Mapped[Decimal] = mapped_column(DINHEIRO, nullable=False)
    trocas: Mapped[Decimal] = mapped_column(DINHEIRO, nullable=False)
    faturamento_liquido: Mapped[Decimal | None] = mapped_column(DINHEIRO, nullable=True)


class DsVendaDiaria(_LinhaDataset, Base):
    __tablename__ = "ds_vendas_diarias"

    data: Mapped[date] = mapped_column(Date, nullable=False)
    vendedor: Mapped[str | None] = mapped_column(String, nullable=True)
    faturamento_bruto: Mapped[Decimal] = mapped_column(DINHEIRO, nullable=False)
    trocas: Mapped[Decimal] = mapped_column(DINHEIRO, nullable=False)
    atendimentos: Mapped[int] = mapped_column(Integer, nullable=False)
    pecas: Mapped[Decimal] = mapped_column(QUANTIDADE, nullable=False)


class DsVendaProdutoPeriodo(_LinhaDataset, Base):
    __tablename__ = "ds_vendas_produto_periodo"

    produto: Mapped[str] = mapped_column(String, nullable=False)
    codigo_produto: Mapped[str | None] = mapped_column(String, nullable=True)
    grupo: Mapped[str] = mapped_column(String, nullable=False, default="")
    familia: Mapped[str] = mapped_column(String, nullable=False, default="")
    quantidade: Mapped[Decimal] = mapped_column(QUANTIDADE, nullable=False)
    receita: Mapped[Decimal] = mapped_column(DINHEIRO, nullable=False)
    custo: Mapped[Decimal | None] = mapped_column(DINHEIRO, nullable=True)


class DsContatoVendedor(_LinhaDataset, Base):
    __tablename__ = "ds_contatos_vendedor"

    vendedor: Mapped[str | None] = mapped_column(String, nullable=True)
    contatos: Mapped[int] = mapped_column(Integer, nullable=False)
    respostas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conversoes: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DsItemVenda(_LinhaDataset, Base):
    __tablename__ = "ds_itens_venda"

    documento: Mapped[str] = mapped_column(String, nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    operacao: Mapped[str] = mapped_column(String, nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(QUANTIDADE, nullable=False)
    valor: Mapped[Decimal] = mapped_column(DINHEIRO, nullable=False)
    produto: Mapped[str] = mapped_column(String, nullable=False, default="")
    codigo_produto: Mapped[str | None] = mapped_column(String, nullable=True)
    grupo: Mapped[str] = mapped_column(String, nullable=False, default="")
    familia: Mapped[str] = mapped_column(String, nullable=False, default="")
    vendedor: Mapped[str | None] = mapped_column(String, nullable=True)
    tamanho: Mapped[str] = mapped_column(String, nullable=False, default="")
    cor: Mapped[str] = mapped_column(String, nullable=False, default="")
    colecao: Mapped[str] = mapped_column(String, nullable=False, default="")
