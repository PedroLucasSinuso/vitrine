from datetime import datetime

from app.infrastructure.db.database import Base
from sqlalchemy import Float, ForeignKey, ForeignKeyConstraint, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column


class HistoricoPreco(Base):
    __tablename__ = "historico_precos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo_chamada: Mapped[str] = mapped_column(String, index=True)
    preco_custo: Mapped[float] = mapped_column(Float, nullable=False)
    preco_venda: Mapped[float] = mapped_column(Float, nullable=False)
    markup: Mapped[float] = mapped_column(Float, nullable=False)
    margem: Mapped[float] = mapped_column(Float, nullable=False)
    data_coleta: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    sync_job_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sync_jobs.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["empresa_id", "codigo_chamada"],
            ["produtos.empresa_id", "produtos.codigo_chamada"],
            ondelete="CASCADE",
        ),
    )
