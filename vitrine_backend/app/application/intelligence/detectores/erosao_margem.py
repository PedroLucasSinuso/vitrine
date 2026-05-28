"""Detector de erosão de margem — produtos com margem caindo vs. período anterior."""
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import OperationType
from app.application.intelligence.detectores.base import Detector
from app.application.intelligence.filtros import get_ignored_groups, filtrar_por_grupo

logger = logging.getLogger(__name__)

LIMITE_ITENS = 10
LIMIAR_QUEDA_MARGEM = 0.05  # 5 pontos percentuais de queda
QTD_MIN_VENDAS = 5  # mínimo de unidades vendidas para considerar


class ErosaoMargemDetector(Detector):
    """Identifica produtos cuja margem bruta caiu na comparação com o período anterior.
    Usa custo unitário do PostgreSQL (TransactionItem.unit_cost), não do SQLite local.
    """

    def detectar(
        self,
        db: Session,
        source: TransactionSource,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        duracao = (data_fim - data_inicio).days or 1
        periodo_anterior_fim = data_inicio - timedelta(days=1)
        periodo_anterior_inicio = periodo_anterior_fim - timedelta(days=duracao)

        atuais = source.get_items(data_inicio, data_fim)
        anteriores = source.get_items(periodo_anterior_inicio, periodo_anterior_fim)

        if not atuais:
            return []

        # Agrega vendas + custo por produto
        def _agregar(itens: list) -> dict[str, dict]:
            agg: dict[str, dict] = {}
            for t in itens:
                if t.operation != OperationType.SALE:
                    continue
                cod = t.product_code
                if cod not in agg:
                    agg[cod] = {"qtd": 0.0, "valor": 0.0, "custo_total": 0.0, "nome": "", "grupo": ""}
                qtd = float(t.quantity or 0)
                agg[cod]["qtd"] += qtd
                agg[cod]["valor"] += float(t.line_total or 0)
                agg[cod]["custo_total"] += float(t.unit_cost or 0) * qtd
                if t.product_name:
                    agg[cod]["nome"] = t.product_name
                if t.group_name:
                    agg[cod]["grupo"] = t.group_name
            for cod in agg:
                d = agg[cod]
                d["preco_medio"] = d["valor"] / d["qtd"] if d["qtd"] > 0 else 0
                d["custo_medio"] = d["custo_total"] / d["qtd"] if d["qtd"] > 0 else 0
            return agg

        agg_atual = _agregar(atuais)
        agg_anterior = _agregar(anteriores)

        resultado = []
        for cod, dados in agg_atual.items():
            if dados["qtd"] < QTD_MIN_VENDAS:
                continue
            anterior = agg_anterior.get(cod)
            if not anterior or anterior["qtd"] < QTD_MIN_VENDAS:
                continue

            custo = dados["custo_medio"]
            if custo <= 0:
                continue
            # Custo > preço médio = dado claramente errado no cadastro (ex: custo de lote,
            # produto composto sem rateio, preenchimento incorreto). Esses produtos poluem
            # a análise com margens negativas absurdas e devem ser ignorados.
            if custo > dados["preco_medio"]:
                continue

            margem_atual = (dados["preco_medio"] - custo) / dados["preco_medio"] if dados["preco_medio"] > 0 else 0
            margem_anterior = (anterior["preco_medio"] - custo) / anterior["preco_medio"] if anterior["preco_medio"] > 0 else 0
            variacao = margem_atual - margem_anterior

            if variacao <= -LIMIAR_QUEDA_MARGEM:
                resultado.append({
                    "codigo": cod,
                    "nome": dados["nome"],
                    "grupo": dados.get("grupo", ""),
                    "margem_anterior": round(margem_anterior * 100, 2),
                    "margem_atual": round(margem_atual * 100, 2),
                    "variacao_pp": round(variacao * 100, 2),
                    "preco_medio_anterior": round(anterior["preco_medio"], 2),
                    "preco_medio_atual": round(dados["preco_medio"], 2),
                })

        resultado.sort(key=lambda x: x["variacao_pp"])

        # Remove grupos ignorados
        ignored = get_ignored_groups(db)
        resultado = filtrar_por_grupo(resultado, ignored)

        return resultado[:LIMITE_ITENS]
