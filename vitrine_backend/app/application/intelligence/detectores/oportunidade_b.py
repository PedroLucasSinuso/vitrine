"""Detector de oportunidades classe B — itens B com potencial de subir para A."""
import logging
from datetime import date
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import OperationType
from app.application.intelligence.detectores.base import Detector

logger = logging.getLogger(__name__)

LIMITE_ITENS = 5
LIMIAR_MARGEM_B = 0.30  # margem mínima para considerar "oportunidade"


class OportunidadeBDetector(Detector):
    """Identifica itens classe B (curva ABC) que têm margem acima da média de A."""

    def detectar(
        self,
        db: Session,
        source: TransactionSource,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        # Tenta usar agregados do source
        abc = source.get_curva_abc_aggregates(data_inicio, data_fim, "produto")
        if abc is None:
            # Fallback: calcula manualmente a partir das transações
            return self._calcular_manual(source, data_inicio, data_fim)

        # Ordena por receita decrescente
        abc.sort(key=lambda x: float(x.get("receita", 0) or 0), reverse=True)
        receita_total = sum(float(x.get("receita", 0) or 0) for x in abc)

        if receita_total <= 0:
            return []

        # Classifica A (acumulado <= 80%), B (<= 95%), C (resto)
        classe_a: list[dict] = []
        classe_b: list[dict] = []
        acumulado = 0.0
        cutoff_a = 0.80 * receita_total
        cutoff_b = 0.95 * receita_total
        for item in abc:
            receita = float(item.get("receita", 0) or 0)
            entry = {
                "codigo": str(item.get("codigo", "")),
                "nome": str(item.get("nome", "")),
                "receita": round(receita, 2),
                "participacao": round(receita / receita_total, 4) if receita_total else 0,
                "margem": float(item.get("margem", 0) or 0),
            }
            if acumulado < cutoff_a:
                classe_a.append(entry)
            elif acumulado < cutoff_b:
                classe_b.append(entry)
            acumulado += receita

        if not classe_b:
            return []

        margem_media_a = sum(x["margem"] for x in classe_a) / len(classe_a) if classe_a else 0

        resultado = []
        for item in classe_b:
            if item["margem"] > margem_media_a and item["margem"] >= LIMIAR_MARGEM_B:
                upside = item["margem"] - margem_media_a
                resultado.append({
                    "codigo": item["codigo"],
                    "nome": item["nome"],
                    "receita": item["receita"],
                    "participacao": item["participacao"],
                    "margem_atual": round(item["margem"] * 100, 2),
                    "margem_media_a": round(margem_media_a * 100, 2),
                    "upside_margem": round(upside * 100, 2),
                    "potencial_ganho_mensal": round(item["receita"] * upside, 2),
                })

        resultado.sort(key=lambda x: x["potencial_ganho_mensal"], reverse=True)
        return resultado[:LIMITE_ITENS]

    def _calcular_manual(
        self,
        source: TransactionSource,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        """Fallback: calcula manualmente a partir de todas as transações."""
        transacoes = source.get_items(data_inicio, data_fim)
        if not transacoes:
            return []

        from collections import defaultdict
        agg: dict[str, dict] = {}
        for t in transacoes:
            if t.operation != OperationType.SALE:
                continue
            cod = t.product_code
            if cod not in agg:
                agg[cod] = {
                    "codigo": cod,
                    "nome": t.product_name or "",
                    "receita": 0.0,
                }
            agg[cod]["receita"] += float(t.line_total or 0)

        if not agg:
            return []

        items = list(agg.values())
        items.sort(key=lambda x: x["receita"], reverse=True)
        receita_total = sum(x["receita"] for x in items)

        if receita_total <= 0:
            return []

        # Classifica A, B manualmente (sem margem — dados insuficientes)
        resultado = []
        for item in items:
            if item["receita"] / receita_total <= 0.15:
                resultado.append(item)

        # Retorna os que têm receita significativa mas não são top
        resultado.sort(key=lambda x: x["receita"], reverse=True)
        return resultado[:LIMITE_ITENS]
