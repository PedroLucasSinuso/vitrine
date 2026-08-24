from app.infrastructure.db.database import Base
from sqlalchemy import Boolean, ForeignKey, ForeignKeyConstraint, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Produto(Base):
    __tablename__ = "produtos"

    # codigo_chamada (PLU/código interno do ERP) só é único DENTRO de uma
    # empresa — duas lojas diferentes podem usar o mesmo código interno
    # para produtos diferentes. Por isso a PK é composta.
    # sem index=True separado: já é o primeiro campo da PK composta, que
    # o SQLite já usa como índice para "WHERE empresa_id = X".
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), primary_key=True
    )
    codigo_chamada: Mapped[str] = mapped_column(String, primary_key=True)

    nome: Mapped[str] = mapped_column(String, index=True)
    grupo: Mapped[str] = mapped_column(String, index=True)
    familia: Mapped[str] = mapped_column(String, index=True)

    preco_venda: Mapped[float] = mapped_column(Float)
    preco_custo: Mapped[float] = mapped_column(Float)
    estoque: Mapped[float] = mapped_column(Float)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

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
    # Denormalizado (em vez de só herdar via join com Produto) para que
    # a busca por código de barras (feita direto nesta tabela — ver
    # ProdutoRepository.obter_por_codigo) possa filtrar por tenant sem
    # depender de ninguém lembrar de fazer o join com Produto primeiro.
    # Esse é justamente o tipo de esquecimento que vaza dado entre clientes.
    empresa_id: Mapped[int] = mapped_column(
        ForeignKey("empresas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo: Mapped[str] = mapped_column(String, index=True)
    codigo_chamada: Mapped[str] = mapped_column(String, nullable=False, index=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["empresa_id", "codigo_chamada"],
            ["produtos.empresa_id", "produtos.codigo_chamada"],
            ondelete="CASCADE",
        ),
    )

    produto = relationship("Produto", back_populates="codigos")