from datetime import date, datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from app.application.bi.loader import carregar_fluxo
from app.application.bi.domain.vendas import Vendas
from app.application.bi.domain.trocas import Trocas
from app.application.bi.schema import COLUNAS
import logging

logger = logging.getLogger(__name__)


def _ajustar_mesmo_dia_semana(data_atual: date, data_alvo: date) -> date:
    """Desloca data_alvo para o mesmo dia da semana de data_atual.

    Deslocamento máximo de ±3 dias (padrão indústria varejo).
    O range resultante pode variar ±1 dia — intencional, evita ruído
    de comparação entre dias da semana diferentes no YoY.
    """
    diff = (data_atual.weekday() - data_alvo.weekday()) % 7
    if diff > 3:
        diff -= 7
    return data_alvo + timedelta(days=diff)


class DominioBI:
    """Contém os domínios de vendas e trocas para o período informado."""
    def __init__(self, vendas: Vendas, trocas: Trocas):
        """Inicializa com os domínios de vendas e trocas."""
        self.vendas = vendas
        self.trocas = trocas


def criar_dominio(data_inicio: date, data_fim: date, db: Session) -> DominioBI:
    """Cria o domínio BI carregando os dados do PostgreSQL para o período."""
    logger.info("BI criando domínio | periodo=%s..%s", data_inicio, data_fim)
    df = carregar_fluxo(data_inicio, data_fim, db)
    vendas = Vendas(df)
    trocas = Trocas(df)
    logger.info("BI domínio criado | periodo=%s..%s vendas=%s trocas=%s",
                data_inicio, data_fim, len(vendas.df), len(trocas.df))
    return DominioBI(vendas=vendas, trocas=trocas)


def criar_dominio_comparativo(data_inicio: date, data_fim: date, db: Session) -> tuple[DominioBI, DominioBI | None]:
    dominio_atual = criar_dominio(data_inicio, data_fim, db)

    # -- Tasks 1+2: ajusta dia da semana + trata 29/02 ---------------------------
    def _calcular_data_ant(data: date) -> date:
        try:
            return _ajustar_mesmo_dia_semana(data, data.replace(year=data.year - 1))
        except ValueError:
            logger.warning(
                "BI YoY | data inválida para year-1, usando day=28 | data=%s", data
            )
            return _ajustar_mesmo_dia_semana(data, data.replace(year=data.year - 1, day=28))

    data_inicio_ant = _calcular_data_ant(data_inicio)
    data_fim_ant = _calcular_data_ant(data_fim)

    if data_fim == date.today():
        hora_atual = datetime.now().hour
        dominio_anterior = criar_dominio(data_inicio_ant, data_fim_ant, db)
        logger.info("BI hora filter | hora_atual=%s data_fim_ant=%s", hora_atual, data_fim_ant)

        # Filtra hora futura no ano anterior
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
                logger.info(
                    "BI hora filter | nome=%s emissao_dtype=%s hora_dtype=%s rows=%s->%s",
                    nome, emissao_dtype, hora_dtype, rows_before, rows_after,
                )

        # -- Task 3: mesmo filtro de hora futura no domínio atual -----------------
        for nome, dominio in (("vendas", dominio_atual.vendas), ("trocas", dominio_atual.trocas)):
            if COLUNAS.hora in dominio.df.columns and COLUNAS.emissao in dominio.df.columns:
                rows_before = len(dominio.df)
                mask = (
                    (dominio.df[COLUNAS.emissao].astype(str) != data_fim.isoformat()) |
                    (pd.to_numeric(dominio.df[COLUNAS.hora].astype(str).str.split(":").str[0], errors="coerce").fillna(0).astype(int) <= hora_atual)
                )
                dominio.df = dominio.df[mask]
                rows_after = len(dominio.df)
                logger.info(
                    "BI hora filter (atual) | nome=%s rows=%s->%s",
                    nome, rows_before, rows_after,
                )

        return dominio_atual, dominio_anterior

    try:
        dominio_anterior = criar_dominio(data_inicio_ant, data_fim_ant, db)
    except Exception:
        dominio_anterior = None

    return dominio_atual, dominio_anterior