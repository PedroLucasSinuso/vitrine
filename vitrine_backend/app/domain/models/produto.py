from app.infrastructure.db.database import Base
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Produto(Base):
    __tablename__ = "produtos"

    codigo_chamada: Mapped[str] = mapped_column(String, primary_key=True)

    nome: Mapped[str] = mapped_column(String, index=True)
    grupo: Mapped[str] = mapped_column(String, index=True)
    familia: Mapped[str] = mapped_column(String, index=True)

    preco_venda: Mapped[float] = mapped_column(Float)
    preco_custo: Mapped[float] = mapped_column(Float)
    estoque: Mapped[float] = mapped_column(Float)

    codigos = relationship("ProdutoCodigo", back_populates="produto", cascade="all, delete-orphan", lazy="selectin")

    @property
    def markup(self) -> float:
        if self.preco_custo == 0:
            return 0.0
        return (self.preco_venda - self.preco_custo) / self.preco_custo

    @property
    def margem(self) -> float:
        if self.preco_venda == 0:
            return 0.0
        return (self.preco_venda - self.preco_custo) / self.preco_venda


class ProdutoCodigo(Base):
    __tablename__ = "produto_codigos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String, index=True)
    codigo_chamada: Mapped[str] = mapped_column(
        String,
        ForeignKey("produtos.codigo_chamada", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    produto = relationship("Produto", back_populates="codigos")