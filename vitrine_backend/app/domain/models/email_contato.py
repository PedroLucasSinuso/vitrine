from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base

class EmailContato(Base):
    __tablename__ = "email_contatos"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
