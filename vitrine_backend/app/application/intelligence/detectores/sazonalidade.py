"""Detector de sazonalidade — produtos com crescimento acentuado vs. período anterior."""
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import OperationType
from app.application.intelligence.detectores.base import Detector
from app.application.intelligence.filtros import get_ignored_groups, filtrar_por_grupo

logger = logging.getLogger(__name__)

LIMITE_ITENS = 10
LIMIAR_CRESCIMENTO = 0.30  # 30% de crescimento


class SazonalidadeDetector(Detector):
    """Identifica produtos com pico sazonal comparando período atual vs. anterior."""

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

        def _agregar(itens: list) -> dict[str, dict]:
            agg: dict[str, dict] = {}
            for t in itens:
                if t.operation != OperationType.SALE:
                    continue
                cod = t.product_code
                if cod not in agg:
                    agg[cod] = {
                        "codigo": cod,
                        "nome": t.product_name or "",
                        "grupo": t.group_name or "",
                        "familia": t.family_name or "",
                        "qtd": 0.0,
                        "valor": 0.0,
                    }
                agg[cod]["qtd"] += float(t.quantity or 0)
                agg[cod]["valor"] += float(t.line_total or 0)
            return agg

        agg_atual = _agregar(atuais)
        agg_anterior = _agregar(anteriores)

        resultado = []
        for cod, dados in agg_atual.items():
            anterior = agg_anterior.get(cod)
            if not anterior or anterior["qtd"] <= 0:
                continue
            crescimento = (dados["qtd"] - anterior["qtd"]) / anterior["qtd"]
            if crescimento >= LIMIAR_CRESCIMENTO:
                dados["crescimento_qtd"] = round(crescimento, 4)
                dados["qtd_anterior"] = int(anterior["qtd"])
                dados["qtd_atual"] = int(dados["qtd"])
                dados["valor_atual"] = round(dados["valor"], 2)
                resultado.append(dados)

        # Ordena por crescimento (decrescente) e limita
        resultado.sort(key=lambda x: x["crescimento_qtd"], reverse=True)

        # Remove grupos ignorados
        ignored = get_ignored_groups(db)
        resultado = filtrar_por_grupo(resultado, ignored)

        return resultado[:LIMITE_ITENS]
