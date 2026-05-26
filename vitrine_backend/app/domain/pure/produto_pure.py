"""ProdutoPuro — dataclass pura sem dependência de SQLAlchemy.

Usada como modelo de domínio desacoplado do ORM. Pode ser usada em testes
unitários sem banco de dados, em regras de negócio, e como resultado de
repositórios "domain-oriented".

A migração do ORM antigo (Produto, SQLAlchemy) para este modelo puro é
gradual: ambos coexistem. O novo repositório (produto_repository_domain)
mapeia ORM → Puro, permitindo que serviços de domínio operem sem
conhecer SQLAlchemy.
"""

from dataclasses import dataclass, field


@dataclass
class ProdutoPuro:
    """Representação pura de um produto, sem vínculo com ORM.

    Attributes:
        codigo_chamada: Código principal do produto (PK no ORM).
        nome: Nome/descrição do produto.
        grupo: Grupo do produto (cru do ERP, pode ser normalizado).
        familia: Família do produto (cru do ERP, pode ser normalizado).
        preco_venda: Preço de venda.
        preco_custo: Preço de custo.
        estoque: Quantidade em estoque.
        ativo: Se o produto está ativo.
        codigos: Lista de códigos adicionais (EAN, PLU, etc.).
    """
    codigo_chamada: str
    nome: str
    grupo: str
    familia: str
    preco_venda: float
    preco_custo: float
    estoque: float
    ativo: bool = True
    codigos: list[str] = field(default_factory=list)

    @property
    def markup(self) -> float:
        """Markup percentual sobre o custo."""
        if self.preco_custo == 0:
            return 0.0
        return round((self.preco_venda - self.preco_custo) / self.preco_custo * 100, 2)

    @property
    def margem(self) -> float:
        """Margem percentual sobre a venda."""
        if self.preco_venda == 0:
            return 0.0
        return round((self.preco_venda - self.preco_custo) / self.preco_venda * 100, 2)
