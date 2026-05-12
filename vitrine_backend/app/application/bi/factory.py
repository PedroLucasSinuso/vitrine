from datetime import date, datetime
from app.application.bi.loader import carregar_fluxo
from app.application.bi.domain.vendas import Vendas
from app.application.bi.domain.trocas import Trocas
import logging

logger = logging.getLogger(__name__)


class DominioBI:
    """ContÃ©m os domÃ­nios de vendas e trocas para o perÃ­odo informado."""
    def __init__(self, vendas: Vendas, trocas: Trocas):
        """Inicializa com os domÃ­nios de vendas e trocas."""
        self.vendas = vendas
        self.trocas = trocas


def criar_dominio(data_inicio: date, data_fim: date) -> DominioBI:
    """Cria o domÃ­nio BI carregando os dados do PostgreSQL para o perÃ­odo."""
    logger.info("BI criando domÃ­nio | periodo=%s..%s", data_inicio, data_fim)
    df = carregar_fluxo(data_inicio, data_fim)
    vendas = Vendas(df)
    trocas = Trocas(df)
    logger.info("BI domÃ­nio criado | periodo=%s..%s vendas=%s trocas=%s",
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
        hora_col = "hora"
        if hora_col in dominio_anterior.vendas.df.columns:
            dominio_anterior.vendas.df = dominio_anterior.vendas.df[
                dominio_anterior.vendas.df[hora_col].astype(str).str.split(":").str[0].astype(int) <= hora_atual
            ]
        return dominio_atual, dominio_anterior

    try:
        dominio_anterior = criar_dominio(data_inicio_ant, data_fim_ant)
    except Exception:
        dominio_anterior = None

    return dominio_atual, dominio_anterior