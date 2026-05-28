"""Detector de taxa de troca — produtos com alta devolução/troca."""
import logging
from datetime import date
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import OperationType
from app.application.intelligence.detectores.base import Detector
from app.application.intelligence.filtros import get_ignored_groups, filtrar_por_grupo

logger = logging.getLogger(__name__)

LIMITE_ITENS = 10
LIMIAR_TAXA_TROCA = 0.10  # 10%


class TaxaTrocaDetector(Detector):
    """Identifica produtos com alta taxa de troca/devolução."""

    def detectar(
        self,
        db: Session,
        source: TransactionSource,
        data_inicio: date,
        data_fim: date,
    ) -> list[dict]:
        transacoes = source.get_items(data_inicio, data_fim)

        if not transacoes:
            return []

        # Agrupa vendas e devoluções por produto
        vendas: dict[str, dict] = {}
        # product_code -> { qtd_vendida, qtd_devolvida, nome, grupo, familia }

        for t in transacoes:
            cod = t.product_code
            if cod not in vendas:
                vendas[cod] = {
                    "codigo": cod,
                    "nome": t.product_name or "",
                    "grupo": t.group_name or "",
                    "familia": t.family_name or "",
                    "qtd_vendida": 0.0,
                    "qtd_devolvida": 0.0,
                    "valor_vendido": 0.0,
                }

            qtd = float(t.quantity or 0)
            valor = float(t.line_total or 0)

            if t.operation == OperationType.SALE:
                vendas[cod]["qtd_vendida"] += qtd
                vendas[cod]["valor_vendido"] += valor
            elif t.operation == OperationType.RETURN:
                vendas[cod]["qtd_devolvida"] += qtd

        # Calcula taxa e filtra
        resultado = []
        for dados in vendas.values():
            qtd_vendida = dados["qtd_vendida"]
            qtd_devolvida = abs(dados["qtd_devolvida"])
            if qtd_vendida <= 0:
                continue
            taxa = qtd_devolvida / (qtd_vendida + qtd_devolvida)
            if taxa >= LIMIAR_TAXA_TROCA:
                dados["taxa"] = round(taxa, 4)
                dados["qtd_trocas"] = int(qtd_devolvida)
                dados["qtd_vendas"] = int(qtd_vendida)
                resultado.append(dados)

        # Ordena por taxa (decrescente) e limita
        resultado.sort(key=lambda x: x["taxa"], reverse=True)

        # Remove grupos ignorados
        ignored = get_ignored_groups(db)
        resultado = filtrar_por_grupo(resultado, ignored)

        return resultado[:LIMITE_ITENS]
