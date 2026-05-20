from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from enum import Enum
from typing import Optional


class OperationType(Enum):
    """Classificação universal de operações de fluxo de mercadorias.

    O adapter mapeia os códigos específicos do ERP para estes 4 tipos.
    Operações não mapeadas retornam None e são ignoradas pelos domínios.
    """
    SALE        = "sale"          # Venda (Alterdata: operacao="V")
    RETURN      = "return"        # Troca/Devolução (Alterdata: operacao="E" + tipo_devolucao in ("T","D"))
    LOSS        = "loss"          # Perda/Quebra (Alterdata: operacao="S" + id_operacao="0RR000000E")
    CONSUMPTION = "consumption"   # Consumo interno (Alterdata: operacao="S" + id_operacao="0103430GOE")


@dataclass(frozen=True)
class TransactionItem:
    # ── Identificação do documento ──
    document_id: str                    # iddocumento (para ticket_medio, qtd_tickets)

    # ── Temporalidade ──
    date: date                          # dtemissao (séries, agrupamento)

    # ── Produto + categorias (análise dimensional) ──
    product_code: str                   # cdprincipal

    # ── Temporalidade (opcional) ──
    time: Optional[time] = None         # hrreferencia (distribuição por hora)

    # ── Classificação (resolvida pelo adapter) ──
    operation: Optional[OperationType] = None  # None = ignorado pelo domínio
    is_canceled: bool = False                   # stdocumentocancelado

    # ── Produto + categorias (opcional) ──
    product_name: str = ""              # dsdetalhe
    group_name: str = ""                # nmgrupo (ex: BEBIDAS)
    family_name: str = ""               # dsfamilia (ex: REFRIGERANTES)

    # ── Métricas ──
    quantity: Decimal = Decimal("0")            # qtitem
    line_total: Decimal = Decimal("0")          # vlmovimento (receita_produto)
    document_total: Decimal = Decimal("0")      # vltotal (total_documento)

    # ── Documento comprobatório ──
    external_document_id: Optional[str] = None
    # Genérico: NF-e, OS, nota de avaria, etc.
    # Usado pelos domínios Perdas/Consumo para filtrar "movimentos documentados"
