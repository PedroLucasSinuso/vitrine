from datetime import date, datetime, timedelta
import logging

from app.core.interfaces.source import TransactionSource
from app.core.models.transaction import TransactionItem
from app.application.bi.domain.vendas import Vendas
from app.application.bi.domain.trocas import Trocas

logger = logging.getLogger(__name__)


def _ajustar_mesmo_dia_semana(data_atual: date, data_alvo: date) -> date:
    """Desloca data_alvo para o mesmo dia da semana de data_atual.
    Deslocamento máximo de ±3 dias (padrão indústria varejo)."""
    diff = (data_atual.weekday() - data_alvo.weekday()) % 7
    if diff > 3:
        diff -= 7
    return data_alvo + timedelta(days=diff)


class DominioBI:
    """Contém os domínios de vendas e trocas para o período informado."""
    def __init__(self, vendas: Vendas, trocas: Trocas):
        self.vendas = vendas
        self.trocas = trocas


def _filtrar_hora(items: list[TransactionItem], data_limite: date, hora_atual: int) -> list[TransactionItem]:
    """Remove itens com hora futura na data_limite (para YoY com dia parcial)."""
    return [
        i for i in items
        if i.date != data_limite
        or (i.time is not None and i.time.hour <= hora_atual)
    ]


def criar_dominio(source: TransactionSource, data_inicio: date, data_fim: date) -> DominioBI:
    """Cria o domínio BI carregando os dados via TransactionSource."""
    logger.info("BI criando domínio | periodo=%s..%s", data_inicio, data_fim)
    items = source.get_items(data_inicio, data_fim)
    vendas = Vendas(items)
    trocas = Trocas(items)
    logger.info("BI domínio criado | periodo=%s..%s vendas=%s trocas=%s",
                data_inicio, data_fim, len(vendas.items), len(trocas.items))
    return DominioBI(vendas=vendas, trocas=trocas)


def criar_dominio_comparativo(
    source: TransactionSource,
    data_inicio: date,
    data_fim: date,
) -> tuple[DominioBI, DominioBI | None]:
    dominio_atual = criar_dominio(source, data_inicio, data_fim)

    def _calcular_data_ant(data: date) -> date:
        try:
            return _ajustar_mesmo_dia_semana(data, data.replace(year=data.year - 1))
        except ValueError:
            logger.warning("BI YoY | data inválida para year-1, usando day=28 | data=%s", data)
            return _ajustar_mesmo_dia_semana(data, data.replace(year=data.year - 1, day=28))

    data_inicio_ant = _calcular_data_ant(data_inicio)
    data_fim_ant = _calcular_data_ant(data_fim)

    if data_fim == date.today():
        hora_atual = datetime.now().hour
        dominio_anterior = criar_dominio(source, data_inicio_ant, data_fim_ant)
        logger.info("BI hora filter | hora_atual=%s data_fim_ant=%s", hora_atual, data_fim_ant)

        # Filtra hora futura no ano anterior
        for nome, dominio_obj in (("vendas", dominio_anterior.vendas), ("trocas", dominio_anterior.trocas)):
            rows_before = len(dominio_obj.items)
            dominio_obj.items = _filtrar_hora(dominio_obj.items, data_fim_ant, hora_atual)
            dominio_obj._df = None  # Invalida cache do DataFrame
            rows_after = len(dominio_obj.items)
            logger.info("BI hora filter | nome=%s rows=%s->%s", nome, rows_before, rows_after)

        # Mesmo filtro de hora futura no domínio atual
        for nome, dominio_obj in (("vendas", dominio_atual.vendas), ("trocas", dominio_atual.trocas)):
            rows_before = len(dominio_obj.items)
            dominio_obj.items = _filtrar_hora(dominio_obj.items, data_fim, hora_atual)
            dominio_obj._df = None
            rows_after = len(dominio_obj.items)
            logger.info("BI hora filter (atual) | nome=%s rows=%s->%s", nome, rows_before, rows_after)

        return dominio_atual, dominio_anterior

    try:
        dominio_anterior = criar_dominio(source, data_inicio_ant, data_fim_ant)
    except Exception:
        dominio_anterior = None

    return dominio_atual, dominio_anterior
