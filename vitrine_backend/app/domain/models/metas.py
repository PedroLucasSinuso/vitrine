from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.database import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class MetaVendedor(Base):
    __tablename__ = "metas_vendedor"
    __table_args__ = (
        UniqueConstraint("empresa_id", "vendedor", "competencia", name="uq_metas_empresa_vendedor_competencia"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    vendedor: Mapped[str] = mapped_column(String, nullable=False)
    competencia: Mapped[str] = mapped_column(String(7), nullable=False)
    valor_meta: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    percentual_comissao: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    atualizado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_agora, onupdate=_agora)


class VendedorAlias(Base):
    __tablename__ = "vendedores_alias"
    __table_args__ = (UniqueConstraint("empresa_id", "nome_origem", name="uq_vendedores_alias_empresa_nome"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False)
    nome_origem: Mapped[str] = mapped_column(String, nullable=False)
    vendedor: Mapped[str] = mapped_column(String, nullable=False)
