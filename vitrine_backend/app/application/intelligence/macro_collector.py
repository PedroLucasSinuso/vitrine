"""Coleta dados macro da loja para enriquecer o prompt da IA."""
from datetime import date
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.application.bi.factory import calcular_kpis_rapido
from app.application.config_service import get
from app.core.config import settings


def coletar_dados_macro(
    db: Session,
    source: TransactionSource,
    data_inicio: date,
    data_fim: date,
) -> dict:
    """Retorna dict com dados macroeconômicos e da loja para o prompt."""
    kpis = calcular_kpis_rapido(source, data_inicio, data_fim)

    cidade = get(db, "cidade", "")
    estado = get(db, "estado", "")
    idh = get(db, "idh_municipio", "")

    faturamento = float(kpis.faturamento_bruto) if kpis else 0
    ticket_medio = float(kpis.ticket_medio) if kpis else 0
    qtd_tickets = int(kpis.qtd_tickets) if kpis else 0

    return {
        "faturamento": faturamento,
        "variacao_faturamento": None,  # preenchido externamente com comparativo
        "ticket_medio": ticket_medio,
        "variacao_ticket": None,
        "qtd_tickets": qtd_tickets,
        "variacao_qtd_tickets": None,
        "margem_media": float(kpis.margem_media) if kpis and hasattr(kpis, "margem_media") else None,
        "top_grupos": "",  # preenchido externamente
        "cidade": cidade,
        "estado": estado,
        "idh": idh,
        "ipca_alimentacao": settings.ipca_alimentacao_12m,
        "selic": settings.selic,
    }
