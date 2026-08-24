"""Model de tenant (empresa/loja cliente do SaaS).

Cada Empresa é um cliente do Vitrine — uma loja/supermercado com seu
próprio ERP, usuários, produtos, inventários, etc. Toda tabela
operacional carrega uma FK `empresa_id` para esta tabela (ver
docs/plano de SaaS multi-tenant).

`Usuario.empresa_id` é a única exceção que pode ser NULL: usuários com
role=super_admin não pertencem a nenhuma empresa — administram a
plataforma (ver RolesEnum.SUPER_ADMIN).
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    # ativa | suspensa — hoje só filtra quais empresas entram nos schedulers
    # (ETL de sync e notificações). Bloquear login/API de uma empresa suspensa
    # ainda NÃO está implementado; entra junto com o billing (Fase 3 do plano
    # de SaaS), que fica em cima deste campo.
    status: Mapped[str] = mapped_column(String, nullable=False, default="ativa")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
