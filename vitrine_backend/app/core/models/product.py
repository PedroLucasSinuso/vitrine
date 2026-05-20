from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Product:
    internal_code: str                 # cdprincipal (PK)
    name: str                          # dsdetalhe
    barcodes: list[str] = field(default_factory=list)  # EAN/PLU (múltiplos)
    sale_price: Decimal = Decimal("0")      # vlprecovenda
    cost_price: Decimal = Decimal("0")      # vlprecocusto (para markup/margem)
    stock: float = 0.0                      # estoque
    group: str = ""                         # nmgrupo (dimensão de análise)
    family: str = ""                        # dsfamilia (dimensão de análise)
    is_active: bool = True                  # explícito; adapter decide o que é "ativo"
