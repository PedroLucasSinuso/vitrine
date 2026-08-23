"""Modelo ORM para normalização de grupos e famílias de produtos.

Armazena mapeamentos de grupo/família originais (crus do ERP) para
valores normalizados. Permite que o operador configure regras de
normalização via admin, sem alterar dados no ERP.

A normalização é aplicada no momento da leitura (query time) ou na
carga (ETL time), conforme decisão arquitetural.
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.db.database import Base


class GrupoFamilia(Base):
    """Mapeamento de grupos e famílias originais para normalizados.

    Attributes:
        id: Identificador único.
        grupo_original: Nome do grupo conforme vindo do ERP.
        familia_original: Nome da família conforme vindo do ERP.
        grupo_normalizado: Nome do grupo após normalização.
        familia_normalizada: Nome da família após normalização.
    """

    __tablename__ = "grupos_familias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    grupo_original: Mapped[str] = mapped_column(String, nullable=False, index=True)
    familia_original: Mapped[str] = mapped_column(String, nullable=False, index=True)
    grupo_normalizado: Mapped[str] = mapped_column(String, nullable=False)
    familia_normalizada: Mapped[str] = mapped_column(String, nullable=False)
