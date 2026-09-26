from datetime import datetime

from app.infrastructure.db.database import Base
from sqlalchemy import Float, ForeignKey, ForeignKeyConstraint, Index, Integer, Numeric, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column


class HistoricoPreco(Base):
    __tablename__ = "historico_precos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False
    )
    codigo_chamada: Mapped[str] = mapped_column(String)
    preco_custo: Mapped[float] = mapped_column(Numeric(14, 4, asdecimal=False), nullable=False)
    preco_venda: Mapped[float] = mapped_column(Numeric(14, 4, asdecimal=False), nullable=False)
    markup: Mapped[float] = mapped_column(Float, nullable=False)
    margem: Mapped[float] = mapped_column(Float, nullable=False)
    data_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sync_job_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sync_jobs.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["empresa_id", "codigo_chamada"],
            ["produtos.empresa_id", "produtos.codigo_chamada"],
            ondelete="CASCADE",
        ),
        Index("ix_historico_precos_empresa_codigo_data", "empresa_id", "codigo_chamada", "data_coleta"),
    )
