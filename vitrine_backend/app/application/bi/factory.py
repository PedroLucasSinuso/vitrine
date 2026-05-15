from datetime import date, datetime
import pandas as pd
from app.application.bi.loader import carregar_fluxo
from app.application.bi.domain.vendas import Vendas
from app.application.bi.domain.trocas import Trocas
from app.application.bi.schema import COLUNAS
import logging

logger = logging.getLogger(__name__)


class DominioBI:
    """Contém os domínios de vendas e trocas para o período informado."""
    def __init__(self, vendas: Vendas, trocas: Trocas):
        """Inicializa com os domínios de vendas e trocas."""
        self.vendas = vendas
        self.trocas = trocas


def criar_dominio(data_inicio: date, data_fim: date) -> DominioBI:
    """Cria o domínio BI carregando os dados do PostgreSQL para o período."""
    logger.info("BI criando domínio | periodo=%s..%s", data_inicio, data_fim)
    df = carregar_fluxo(data_inicio, data_fim)
    vendas = Vendas(df)
    trocas = Trocas(df)
    logger.info("BI domínio criado | periodo=%s..%s vendas=%s trocas=%s",
                data_inicio, data_fim, len(vendas.df), len(trocas.df))
    return DominioBI(vendas=vendas, trocas=trocas)


def criar_dominio_comparativo(data_inicio: date, data_fim: date) -> tuple[DominioBI, DominioBI | None]:
    dominio_atual = criar_dominio(data_inicio, data_fim)

    try:
        data_inicio_ant = data_inicio.replace(year=data_inicio.year - 1)
        data_fim_ant = data_fim.replace(year=data_fim.year - 1)
    except ValueError:
        return dominio_atual, None

    if data_fim == date.today():
        hora_atual = datetime.now().hour
        dominio_anterior = criar_dominio(data_inicio_ant, data_fim_ant)
        logger.info("BI hora filter | hora_atual=%s data_fim_ant=%s", hora_atual, data_fim_ant)
        for nome, dominio in (("vendas", dominio_anterior.vendas), ("trocas", dominio_anterior.trocas)):
            if COLUNAS.hora in dominio.df.columns and COLUNAS.emissao in dominio.df.columns:
                rows_before = len(dominio.df)
                emissao_dtype = dominio.df[COLUNAS.emissao].dtype
                hora_dtype = dominio.df[COLUNAS.hora].dtype
                mask = (
                    (dominio.df[COLUNAS.emissao].astype(str) != data_fim_ant.isoformat()) |
                    (pd.to_numeric(dominio.df[COLUNAS.hora].astype(str).str.split(":").str[0], errors="coerce").fillna(0).astype(int) <= hora_atual)
                )
                dominio.df = dominio.df[mask]
                rows_after = len(dominio.df)
                logger.warning(
                    "BI hora filter | nome=%s emissao_dtype=%s hora_dtype=%s rows=%s->%s",
                    nome, emissao_dtype, hora_dtype, rows_before, rows_after,
                )
        return dominio_atual, dominio_anterior

    try:
        dominio_anterior = criar_dominio(data_inicio_ant, data_fim_ant)
    except Exception:
        dominio_anterior = None

    return dominio_atual, dominio_anterior