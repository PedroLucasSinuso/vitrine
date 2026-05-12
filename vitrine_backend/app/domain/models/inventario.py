from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class SessaoInventario(Base):
    __tablename__ = "sessoes_inventario"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    criado_por_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ativa", index=True)
    codigo_convite: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    encerrado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ItemInventario(Base):
    __tablename__ = "itens_inventario"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sessao_id: Mapped[int] = mapped_column(ForeignKey("sessoes_inventario.id"), nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    grupo: Mapped[str] = mapped_column(String, nullable=False)
    familia: Mapped[str] = mapped_column(String, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("sessao_id", "usuario_id", "codigo", name="uq_sessao_usuario_codigo"),
    )