"""Coleta dados macro da loja para enriquecer o prompt da IA."""
import asyncio
from datetime import date
from sqlalchemy.orm import Session
from app.core.interfaces.source import TransactionSource
from app.application.bi.factory import calcular_kpis_rapido
from app.application.config_service import get


def coletar_dados_macro(
    db: Session,
    source: TransactionSource,
    data_inicio: date,
    data_fim: date,
) -> dict:
    """Retorna dict com dados macroeconômicos e da loja para o prompt.

    Indicadores macroeconômicos (IPCA, Selic, etc) são buscados ao vivo
    do Banco Central (BC SGS API) — sem valores hardcoded.
    """
    from app.application.intelligence.macro_fetcher import fetch_todos_indicadores

    kpis = calcular_kpis_rapido(source, data_inicio, data_fim)

    cidade = get(db, "cidade", "")
    estado = get(db, "estado", "")
    idh = get(db, "idh_municipio", "")

    faturamento = float(kpis.faturamento_bruto) if kpis else 0
    ticket_medio = float(kpis.ticket_medio) if kpis else 0
    qtd_tickets = int(kpis.qtd_tickets) if kpis else 0

    # Fetch live macro indicators from BC SGS API
    indicadores = asyncio.run(fetch_todos_indicadores(db))

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
        "indicadores": {
            k: {
                "chave": v.chave,
                "rotulo": v.rotulo,
                "valor": v.valor,
                "disponivel": v.disponivel,
                "unidade": v.unidade,
                "periodo_ref": v.periodo_ref_rotulo,
                "consultado_em": v.consultado_em.isoformat(),
                "mensagem": v.mensagem,
            }
            for k, v in indicadores.items()
        },
    }
