"""Detector de oportunidades classe B — itens B com potencial de subir para A."""
import logging
from datetime import date
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import OperationType
from app.application.intelligence.detectores.base import Detector
from app.application.intelligence.filtros import get_ignored_groups, filtrar_por_grupo

logger = logging.getLogger(__name__)

LIMITE_ITENS = 5
LIMIAR_MARGEM_B = 0.30  # margem mínima para considerar "oportunidade"


def _mediana(valores: list[float]) -> float:
    """Retorna mediana de uma lista de floats. Lista vazia retorna 0."""
    if not valores:
        return 0.0
    sorted_vals = sorted(valores)
    n = len(sorted_vals)
    if n % 2 == 1:
        return sorted_vals[n // 2]
    return (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0


def _calcular_referencia_a(classe_a: list[dict]) -> tuple[float | None, list[dict]]:
    """Calcula margem de referência da classe A usando mediana.
    
    Filtra produtos com margem > 0 (elimina dados sujos do cadastro 
    onde custo > preço de venda). Retorna (margem_ref, classe_a_valida).
    Retorna (None, []) se classe_a ficar vazia após o filtro.
    """
    classe_a_valida = [x for x in classe_a if x["margem"] > 0]
    if not classe_a_valida:
        logger.warning(
            "OportunidadeB: todos produtos A com margem negativa — "
            "dados de custo suspeitos, abortando"
        )
        return (None, [])
    
    margens = [x["margem"] for x in classe_a_valida]
    return (_mediana(margens), classe_a_valida)


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
            return self._calcular_manual(db, source, data_inicio, data_fim)

        # Ordena por receita decrescente
        # NOTA: get_dimensao_aggregates retorna "valor" como chave da métrica
        abc.sort(key=lambda x: float(x.get("valor", x.get("receita", 0)) or 0), reverse=True)
        receita_total = sum(float(x.get("valor", x.get("receita", 0)) or 0) for x in abc)

        if receita_total <= 0:
            return []

        # Classifica A (acumulado <= 80%), B (<= 95%), C (resto)
        classe_a: list[dict] = []
        classe_b: list[dict] = []
        acumulado = 0.0
        cutoff_a = 0.80 * receita_total
        cutoff_b = 0.95 * receita_total
        for item in abc:
            receita = float(item.get("valor", item.get("receita", 0)) or 0)
            entry = {
                "codigo": str(item.get("codigo", "")),
                "nome": str(item.get("produto", item.get("nome", ""))),
                "grupo": str(item.get("grupo", "")),
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

        margem_ref, classe_a_valida = _calcular_referencia_a(classe_a)
        if margem_ref is None:
            return []
        margem_ref_a = margem_ref

        resultado = []
        for item in classe_b:
            if item["margem"] > margem_ref_a and item["margem"] >= LIMIAR_MARGEM_B:
                upside = item["margem"] - margem_ref_a
                resultado.append({
                    "codigo": item["codigo"],
                    "nome": item["nome"],
                    "grupo": item.get("grupo", ""),
                    "receita": item["receita"],
                    "participacao": item["participacao"],
                    "margem_atual": round(item["margem"] * 100, 2),
                    "margem_media_a": round(margem_ref_a * 100, 2),
                    "upside_margem": round(upside * 100, 2),
                    "potencial_ganho_mensal": round(item["receita"] * upside, 2),
                })

        resultado.sort(key=lambda x: x["potencial_ganho_mensal"], reverse=True)

        # Remove grupos ignorados
        ignored = get_ignored_groups(db)
        resultado = filtrar_por_grupo(resultado, ignored)

        return resultado[:LIMITE_ITENS]

    def _calcular_manual(
        self,
        db: Session,
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
                    "custo_total": 0.0,
                    "qtd": 0.0,
                }
            qtd = float(t.quantity or 0)
            agg[cod]["receita"] += float(t.line_total or 0)
            agg[cod]["custo_total"] += float(t.unit_cost or 0) * qtd
            agg[cod]["qtd"] += qtd

        if not agg:
            return []

        # Adiciona margem a cada item
        items = []
        for v in agg.values():
            preco_medio = v["receita"] / v["qtd"] if v["qtd"] > 0 else 0
            custo_medio = v["custo_total"] / v["qtd"] if v["qtd"] > 0 else 0
            margem = (preco_medio - custo_medio) / preco_medio if preco_medio > 0 and custo_medio > 0 else 0
            items.append({
                "codigo": v["codigo"],
                "nome": v["nome"],
                "grupo": v.get("grupo", ""),
                "receita": v["receita"],
                "margem": margem,
            })

        items.sort(key=lambda x: x["receita"], reverse=True)
        receita_total = sum(x["receita"] for x in items)

        if receita_total <= 0:
            return []

        # Classifica A (acumulado <= 80%), B (<= 95%), C (resto)
        classe_a: list[dict] = []
        classe_b: list[dict] = []
        acumulado = 0.0
        cutoff_a = 0.80 * receita_total
        cutoff_b = 0.95 * receita_total
        for item in items:
            receita = item["receita"]
            entry = {
                "codigo": item["codigo"],
                "nome": item["nome"],
                "grupo": item.get("grupo", ""),
                "receita": round(receita, 2),
                "participacao": round(receita / receita_total, 4) if receita_total else 0,
                "margem": item["margem"],
            }
            if acumulado < cutoff_a:
                classe_a.append(entry)
            elif acumulado < cutoff_b:
                classe_b.append(entry)
            acumulado += receita

        if not classe_b:
            return []

        margem_ref, _classe_a_valida = _calcular_referencia_a(classe_a)
        if margem_ref is None:
            return []
        margem_ref_a = margem_ref

        resultado = []
        for item in classe_b:
            if item["margem"] > margem_ref_a and item["margem"] >= LIMIAR_MARGEM_B:
                upside = item["margem"] - margem_ref_a
                resultado.append({
                    "codigo": item["codigo"],
                    "nome": item["nome"],
                    "grupo": item.get("grupo", ""),
                    "receita": item["receita"],
                    "participacao": item["participacao"],
                    "margem_atual": round(item["margem"] * 100, 2),
                    "margem_media_a": round(margem_ref_a * 100, 2),
                    "upside_margem": round(upside * 100, 2),
                    "potencial_ganho_mensal": round(item["receita"] * upside, 2),
                })

        resultado.sort(key=lambda x: x["potencial_ganho_mensal"], reverse=True)

        # Remove grupos ignorados
        ignored = get_ignored_groups(db)
        resultado = filtrar_por_grupo(resultado, ignored)

        return resultado[:LIMITE_ITENS]
