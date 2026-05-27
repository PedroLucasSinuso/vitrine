import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from cachetools import TTLCache
from sqlalchemy import text

logger = logging.getLogger(__name__)

from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import TransactionItem, OperationType
from app.adapters.alterdata.config import OPERATION_MAP, CANCELED_MARKER


_cache: TTLCache = TTLCache(maxsize=32, ttl=300)  # TTL baixo (5 min) para evitar dados obsoletos após sync


class AlterdataTransactionSource(TransactionSource):
    _QUERY_DIR = Path(__file__).resolve().parent / "queries"

    def __init__(self, engine):
        self._engine = engine
        self._fluxo_sql = self._load_query("fluxo")

    def _load_query(self, name: str) -> str:
        path = self._QUERY_DIR / f"{name}.sql"
        return path.read_text(encoding="utf-8")

    def get_items(self, start: date, end: date) -> list[TransactionItem]:
        key = (start.isoformat(), end.isoformat(), "items")
        if key in _cache:
            return _cache[key]

        with self._engine.connect() as conn:
            result = conn.execute(
                text(self._fluxo_sql),
                {"data_inicio": start.isoformat(), "data_fim": end.isoformat()},
            )
            rows = result.mappings().fetchall()

        items = [self._to_item(r) for r in rows]
        _cache[key] = items
        return items

    def get_kpi_aggregates(self, start: date, end: date) -> dict | None:
        """Retorna agregados de KPI via SQL para evitar carregar todas as linhas.

        Query usa CTEs para agregar vendas e trocas em 2 passadas (documento
        em vez de item), reduzindo drasticamente a quantidade de dados trafegados.
        """
        sql = text("""
            WITH vendas_doc AS (
                SELECT
                    d.iddocumento,
                    d.vltotal,
                    SUM(doc.vlmovimento) AS receita_bruta,
                    SUM(doc.qtitem) AS qtd_itens
                FROM wshop.documen d
                JOIN wshop.docitem doc ON doc.iddocumento = d.iddocumento
                WHERE d.dtemissao >= :data_inicio
                  AND d.dtemissao <= :data_fim
                  AND d.tpoperacao = 'V'
                  AND COALESCE(d.stdocumentocancelado, '') != '*'
                GROUP BY d.iddocumento, d.vltotal
            ),
            trocas_doc AS (
                SELECT
                    d.iddocumento,
                    SUM(ABS(doc.vlmovimento)) AS valor_troca
                FROM wshop.documen d
                JOIN wshop.docitem doc ON doc.iddocumento = d.iddocumento
                WHERE d.dtemissao >= :data_inicio
                  AND d.dtemissao <= :data_fim
                  AND d.tpoperacao = 'E'
                  AND d.tpdevolucao IN ('T','D')
                  AND COALESCE(d.stdocumentocancelado, '') != '*'
                GROUP BY d.iddocumento
            )
            SELECT
                COUNT(v.iddocumento)::int AS qtd_tickets,
                COALESCE(SUM(v.receita_bruta), 0) AS faturamento_bruto,
                COALESCE((SELECT SUM(t.valor_troca) FROM trocas_doc t), 0) AS total_trocas,
                COALESCE(AVG(v.vltotal), 0) AS ticket_medio,
                COALESCE(AVG(v.qtd_itens), 0) AS itens_por_ticket
            FROM vendas_doc v
        """)
        try:
            with self._engine.connect() as conn:
                row = conn.execute(sql, {
                    "data_inicio": start.isoformat(),
                    "data_fim": end.isoformat(),
                }).mappings().one()
            return {
                "faturamento_bruto": float(row["faturamento_bruto"]),
                "total_trocas": float(row["total_trocas"]),
                "qtd_tickets": int(row["qtd_tickets"]),
                "ticket_medio": float(row["ticket_medio"]),
                "itens_por_ticket": float(row["itens_por_ticket"]),
            }
        except Exception:
            logger.exception("BI KPI aggregates | erro na query agregada, fallback para full load")
            return None

    @staticmethod
    def _fmt_date(val) -> str:
        """Converte valor date/datetime para string ISO 'YYYY-MM-DD'."""
        if isinstance(val, datetime):
            return val.date().isoformat()
        if isinstance(val, date):
            return val.isoformat()
        return str(val)

    def get_dimensao_aggregates(self, start: date, end: date, dimensao: str, metrica: str) -> list[dict] | None:
        col_metrica = "SUM(doc.vlmovimento) AS valor" if metrica == "receita" else "SUM(doc.qtitem) AS valor"
        try:
            if dimensao == "produto":
                sql = text(f"""
                    SELECT doc.cdproduto AS codigo,
                           p.nmproduto AS produto,
                           p.nmgrupo AS grupo,
                           p.nmfamilia AS familia,
                           {col_metrica}
                    FROM wshop.documen d
                    JOIN wshop.docitem doc ON doc.iddocumento = d.iddocumento
                    LEFT JOIN wshop.produto p ON p.cdproduto = doc.cdproduto
                    WHERE d.dtemissao >= :data_inicio
                      AND d.dtemissao <= :data_fim
                      AND d.tpoperacao = 'V'
                      AND COALESCE(d.stdocumentocancelado, '') != '*'
                    GROUP BY doc.cdproduto, p.nmproduto, p.nmgrupo, p.nmfamilia
                    ORDER BY valor DESC
                """)
            else:
                group_col = "p.nmgrupo" if dimensao == "grupo" else "p.nmfamilia"
                sql = text(f"""
                    SELECT {group_col} AS dimensao,
                           {col_metrica}
                    FROM wshop.documen d
                    JOIN wshop.docitem doc ON doc.iddocumento = d.iddocumento
                    LEFT JOIN wshop.produto p ON p.cdproduto = doc.cdproduto
                    WHERE d.dtemissao >= :data_inicio
                      AND d.dtemissao <= :data_fim
                      AND d.tpoperacao = 'V'
                      AND COALESCE(d.stdocumentocancelado, '') != '*'
                    GROUP BY {group_col}
                    ORDER BY valor DESC
                """)
            with self._engine.connect() as conn:
                rows = conn.execute(sql, {"data_inicio": start.isoformat(), "data_fim": end.isoformat()}).mappings().fetchall()
            return [dict(r) for r in rows]
        except Exception:
            logger.exception("BI %s aggregates | erro na query agregada", dimensao)
            return None

    def get_diario_aggregates(self, start: date, end: date, metrica: str) -> list[dict] | None:
        col_metrica = "SUM(doc.vlmovimento) AS valor" if metrica == "receita" else "SUM(doc.qtitem) AS valor"
        sql = text(f"""
            SELECT d.dtemissao AS data,
                   {col_metrica}
            FROM wshop.documen d
            JOIN wshop.docitem doc ON doc.iddocumento = d.iddocumento
            WHERE d.dtemissao >= :data_inicio
              AND d.dtemissao <= :data_fim
              AND d.tpoperacao = 'V'
              AND COALESCE(d.stdocumentocancelado, '') != '*'
            GROUP BY d.dtemissao
            ORDER BY d.dtemissao
        """)
        try:
            with self._engine.connect() as conn:
                rows = conn.execute(sql, {"data_inicio": start.isoformat(), "data_fim": end.isoformat()}).mappings().fetchall()
            return [{"data": self._fmt_date(r["data"]), "valor": float(r["valor"])} for r in rows]
        except Exception:
            logger.exception("BI diario aggregates | erro na query agregada")
            return None

    def get_curva_abc_aggregates(self, start: date, end: date, dimensao: str) -> list[dict] | None:
        return self.get_dimensao_aggregates(start, end, dimensao, "receita")

    def get_hora_aggregates(self, start: date, end: date, metrica: str) -> list[dict] | None:
        """Retorna distribuição de vendas por hora via SQL agregado."""
        col = "doc.vlmovimento" if metrica == "receita" else "doc.qtitem"
        sql = text(f"""
            SELECT
                LPAD(EXTRACT(HOUR FROM d.hrreferencia)::int::text, 2, '0') AS hora,
                SUM({col}) AS valor
            FROM wshop.documen d
            JOIN wshop.docitem doc ON doc.iddocumento = d.iddocumento
            WHERE d.dtemissao >= :data_inicio
              AND d.dtemissao <= :data_fim
              AND d.tpoperacao = 'V'
              AND COALESCE(d.stdocumentocancelado, '') != '*'
              AND d.hrreferencia IS NOT NULL
            GROUP BY EXTRACT(HOUR FROM d.hrreferencia)
            ORDER BY hora
        """)
        try:
            with self._engine.connect() as conn:
                rows = conn.execute(sql, {
                    "data_inicio": start.isoformat(),
                    "data_fim": end.isoformat(),
                }).mappings().fetchall()
            return [{"hora": r["hora"], "valor": float(r["valor"])} for r in rows]
        except Exception:
            logger.exception("BI hora aggregates | erro na query agregada, fallback para full load")
            return None

    def _to_item(self, row: dict) -> TransactionItem:
        operacao_raw = row["operacao"]
        devolucao_raw = row.get("tipo_devolucao") or None
        id_operacao_raw = row.get("id_operacao") or ""

        if operacao_raw == "S":
            op_key = (operacao_raw, id_operacao_raw)
        else:
            op_key = (operacao_raw, devolucao_raw if devolucao_raw in ("T", "D") else None)

        operation = OPERATION_MAP.get(op_key)

        emissao = row["emissao"]
        hora = row.get("hora")
        # Normaliza tipos: SQLAlchemy pode retornar datetime no lugar de date
        if isinstance(emissao, datetime):
            emissao = emissao.date()
        if isinstance(hora, datetime):
            hora = hora.time()

        return TransactionItem(
            document_id=str(row["iddocumento"]),
            date=emissao,
            time=hora,
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
