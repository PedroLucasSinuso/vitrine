from datetime import datetime
from pathlib import Path
from decimal import Decimal

from sqlalchemy import text

from app.core.interfaces.source import ProductSource
from app.core.models.product import Product


class AlterdataProductSource(ProductSource):
    _QUERY_DIR = Path(__file__).resolve().parent / "queries"

    def __init__(self, engine):
        self._engine = engine
        self._produto_sql = self._load_query("produto")
        self._codigo_sql = self._load_query("codigo")

    def _load_query(self, name: str) -> str:
        path = self._QUERY_DIR / f"{name}.sql"
        return path.read_text(encoding="utf-8")

    def get_all_products(self) -> list[Product]:
        with self._engine.connect() as conn:
            produtos_raw = conn.execute(text(self._produto_sql)).fetchall()
            codigos_raw = conn.execute(text(self._codigo_sql)).fetchall()

        # Agrupa códigos de barras por produto
        barcodes_map: dict[str, list[str]] = {}
        for row in codigos_raw:
            chave = str(row["codigo_chamada"])
            codigo = str(row["codigo"])
            if codigo:
                barcodes_map.setdefault(chave, []).append(codigo)

        return [
            Product(
                internal_code=str(row["codigo_chamada"]),
                name=str(row["nome"]),
                barcodes=barcodes_map.get(str(row["codigo_chamada"]), []),
                sale_price=Decimal(str(row["preco_venda"])),
                cost_price=Decimal(str(row["preco_custo"])),
                stock=float(row["estoque"]),
                group=str(row["grupo"]),
                family=str(row["familia"]),
                is_active=True,
            )
            for row in produtos_raw
        ]

    def get_products_updated_since(self, since: datetime) -> list[Product]:
        # Versão inicial: Alterdata não tem coluna de atualização confiável
        # Então faz full reload. ERPs modernos podem sobrescrever este método.
        return self.get_all_products()
