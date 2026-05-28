"""Pure Python dataclass for macro-economic indicators (not ORM)."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MacroIndicator:
    chave: str
    rotulo: str
    valor: float | None
    disponivel: bool
    unidade: str
    periodo_ref: str | None
    periodo_ref_rotulo: str | None
    consultado_em: datetime
    mensagem: str | None
    tipo_fonte: str
