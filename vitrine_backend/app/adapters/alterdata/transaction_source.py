from datetime import date
from decimal import Decimal
from pathlib import Path

from cachetools import TTLCache
from sqlalchemy import text

from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import TransactionItem, OperationType
from app.adapters.alterdata.config import OPERATION_MAP, CANCELED_MARKER


_cache: TTLCache = TTLCache(maxsize=32, ttl=3600)


class AlterdataTransactionSource(TransactionSource):
    _QUERY_DIR = Path(__file__).resolve().parent / "queries"

    def __init__(self, engine):
        self._engine = engine
        self._fluxo_sql = self._load_query("fluxo")

    def _load_query(self, name: str) -> str:
        path = self._QUERY_DIR / f"{name}.sql"
        return path.read_text(encoding="utf-8")

    def get_items(self, start: date, end: date) -> list[TransactionItem]:
        key = (start.isoformat(), end.isoformat())
        if key in _cache:
            return _cache[key]

        with self._engine.connect() as conn:
            rows = conn.execute(
                text(self._fluxo_sql),
                {"data_inicio": start.isoformat(), "data_fim": end.isoformat()},
            ).fetchall()

        items = [self._to_item(r) for r in rows]
        _cache[key] = items
        return items

    def _to_item(self, row: dict) -> TransactionItem:
        operacao_raw = row["operacao"]
        devolucao_raw = row.get("tipo_devolucao") or None
        id_operacao_raw = row.get("id_operacao") or ""

        if operacao_raw == "S":
            op_key = (operacao_raw, id_operacao_raw)
        else:
            op_key = (operacao_raw, devolucao_raw if devolucao_raw in ("T", "D") else None)

        operation = OPERATION_MAP.get(op_key)

        return TransactionItem(
            document_id=str(row["iddocumento"]),
            date=row["emissao"],
            time=row.get("hora"),
            operation=operation,
            is_canceled=row.get("cancelado") == CANCELED_MARKER,
            product_code=str(row["codigo"]),
            product_name=str(row["produto"]),
            group_name=str(row.get("grupo") or ""),
            family_name=str(row.get("familia") or ""),
            quantity=Decimal(str(row["qtd_item"])),
            line_total=Decimal(str(row["receita_produto"])),
            document_total=Decimal(str(row.get("total_documento", 0))),
            external_document_id=row.get("id_nfe") or None,
        )

    def invalidar_cache(self) -> None:
        _cache.clear()


def invalidar_cache_transacoes() -> None:
    """Função pública para invalidar o cache de transações.
    Útil para background jobs (sync) que não têm acesso à instância do adapter."""
    _cache.clear()
