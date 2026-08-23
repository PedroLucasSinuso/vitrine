from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class Configuracao(Base):
    __tablename__ = "configuracoes"

    # Cada empresa tem sua própria config de ERP, Twilio, SMTP etc — a
    # PK composta garante que a mesma "chave" (ex: erp_password) tem um
    # valor por empresa, não um valor global compartilhado.
    # sem index=True separado: já é o primeiro campo da PK composta.
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), primary_key=True
    )
    chave: Mapped[str] = mapped_column(String, primary_key=True)
    valor: Mapped[str] = mapped_column(String, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
