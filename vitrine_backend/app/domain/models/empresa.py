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
from sqlalchemy import CheckConstraint, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.domain.enums import ModoOperacao, Segmento
from app.infrastructure.db.database import Base


class Empresa(Base):
    __tablename__ = "empresas"
    __table_args__ = (
        CheckConstraint("status IN ('ativa', 'suspensa')", name="ck_empresas_status"),
        CheckConstraint(
            "segmento IN ({})".format(", ".join(f"'{s.value}'" for s in Segmento)),
            name="ck_empresas_segmento",
        ),
        CheckConstraint(
            "modo IN ({})".format(", ".join(f"'{m.value}'" for m in ModoOperacao)),
            name="ck_empresas_modo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    # ativa | suspensa — hoje só filtra quais empresas entram nos schedulers
    # (ETL de sync e notificações). Bloquear login/API de uma empresa suspensa
    # ainda NÃO está implementado; entra junto com o billing (Fase 3 do plano
    # de SaaS), que fica em cima deste campo.
    status: Mapped[str] = mapped_column(String, nullable=False, default="ativa")
    segmento: Mapped[str] = mapped_column(
        String, nullable=False, default=Segmento.SUPERMERCADO.value, server_default=Segmento.SUPERMERCADO.value
    )
    modo: Mapped[str] = mapped_column(
        String, nullable=False, default=ModoOperacao.LEGADO.value, server_default=ModoOperacao.LEGADO.value
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
