from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # username permanece ÚNICO GLOBALMENTE (não por empresa) de propósito:
    # o login (POST /auth/token) só recebe username+senha, sem seletor de
    # empresa/subdomínio. Onboarding é assistido (você provisiona cada
    # usuário), então evitar colisão é trivial operacionalmente. Se algum
    # dia o cadastro virar self-service, isso precisa de um seletor de
    # workspace/subdomínio no login — reavaliar nessa hora.
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    nome_exibicao: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    token_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # NULL apenas para role=super_admin (não pertence a nenhuma empresa).
    empresa_id: Mapped[int | None] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=True, index=True
    )