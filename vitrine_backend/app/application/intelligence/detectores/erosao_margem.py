"""Detector de erosão de margem — produtos com margem caindo vs. período anterior."""
import logging
from collections import defaultdict
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import OperationType
from app.application.intelligence.detectores.base import Detector
from app.domain.models.produto import Produto

logger = logging.getLogger(__name__)

LIMITE_ITENS = 10
LIMIAR_QUEDA_MARGEM = 0.05  # 5 pontos percentuais de queda
QTD_MIN_VENDAS = 5  # mínimo de unidades vendidas para considerar


class ErosaoMargemDetector(Detector):
    """Identifica produtos cuja margem bruta caiu na comparação com o período anterior."""

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

        # Agrega vendas por produto
        def _agregar(itens: list) -> dict[str, dict]:
            agg: dict[str, dict] = {}
            for t in itens:
                if t.operation != OperationType.SALE:
                    continue
                cod = t.product_code
                if cod not in agg:
                    agg[cod] = {"qtd": 0.0, "valor": 0.0}
                qtd = float(t.quantity or 0)
                agg[cod]["qtd"] += qtd
                agg[cod]["valor"] += float(t.line_total or 0)
                agg[cod]["preco_medio"] = agg[cod]["valor"] / agg[cod]["qtd"] if agg[cod]["qtd"] > 0 else 0
            return agg

        agg_atual = _agregar(atuais)
        agg_anterior = _agregar(anteriores)

        # Busca custo dos produtos do DB
        codigos = set(agg_atual.keys()) | set(agg_anterior.keys())
        produtos_db = (
            db.query(Produto)
            .filter(Produto.codigo_chamada.in_(codigos))  # type: ignore
            .all()
        )
        custos: dict[str, float] = {p.codigo_chamada: float(p.preco_custo or 0) for p in produtos_db}

        resultado = []
        for cod, dados in agg_atual.items():
            if dados["qtd"] < QTD_MIN_VENDAS:
                continue
            anterior = agg_anterior.get(cod)
            if not anterior or anterior["qtd"] < QTD_MIN_VENDAS:
                continue

            custo = custos.get(cod, 0)
            if custo <= 0:
                continue

            margem_atual = (dados["preco_medio"] - custo) / dados["preco_medio"] if dados["preco_medio"] > 0 else 0
            margem_anterior = (anterior["preco_medio"] - custo) / anterior["preco_medio"] if anterior["preco_medio"] > 0 else 0
            variacao = margem_atual - margem_anterior

            if variacao <= -LIMIAR_QUEDA_MARGEM:
                nome = ""
                if cod in agg_atual:
                    for t in atuais:
                        if t.product_code == cod and t.product_name:
                            nome = t.product_name
                            break
                resultado.append({
                    "codigo": cod,
                    "nome": nome,
                    "margem_anterior": round(margem_anterior * 100, 2),
                    "margem_atual": round(margem_atual * 100, 2),
                    "variacao_pp": round(variacao * 100, 2),
                    "preco_medio_anterior": round(anterior["preco_medio"], 2),
                    "preco_medio_atual": round(dados["preco_medio"], 2),
                })

        resultado.sort(key=lambda x: x["variacao_pp"])
        return resultado[:LIMITE_ITENS]
