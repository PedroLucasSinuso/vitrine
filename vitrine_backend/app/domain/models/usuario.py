from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    nome_exibicao: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )