from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base

class WhatsAppContato(Base):
    __tablename__ = "whatsapp_contatos"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
