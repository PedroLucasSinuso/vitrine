from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal
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
        or i.time is None
        or i.time.hour <= hora_atual
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


def _debug_items(items_before: list[TransactionItem], data_limite: date, hora_atual: int, label: str):
    """Log detalhado para depuração do filtro de hora."""
    filtrados = _filtrar_hora(items_before, data_limite, hora_atual)

    # Contagem por data no período
    datas = Counter(i.date for i in items_before)
    soma_total = sum(float(i.line_total) for i in items_before if isinstance(i.line_total, (int, float, Decimal)))
    soma_filtrada = sum(float(i.line_total) for i in filtrados if isinstance(i.line_total, (int, float, Decimal)))

    logger.info(
        "BI debug | %s hora_atual=%s data_limite=%s "
        "items=%s filtrados=%s "
        "soma_total=%.2f soma_filtrada=%.2f "
        "datas=%s",
        label, hora_atual, data_limite,
        len(items_before), len(filtrados),
        soma_total, soma_filtrada,
        dict(datas),
    )

    # Detalhe da data limite
    itens_na_data = [i for i in items_before if i.date == data_limite]
    com_time = sum(1 for i in itens_na_data if i.time is not None)
    sem_time = sum(1 for i in itens_na_data if i.time is None)
    soma_data = sum(float(i.line_total) for i in itens_na_data if isinstance(i.line_total, (int, float, Decimal)))
    logger.info(
        "BI debug | %s data_limite=%s itens_na_data=%s "
        "com_time=%s sem_time=%s soma_total=%.2f",
        label, data_limite, len(itens_na_data), com_time, sem_time, soma_data,
    )

    # Distribuição de horas na data limite
    if itens_na_data:
        horas = Counter(i.time.hour for i in itens_na_data if i.time is not None)
        logger.info("BI debug | %s horas na data_limite=%s", label, dict(sorted(horas.items())))


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

    logger.info(
        "BI comparativo | periodo_atual=%s..%s periodo_ant=%s..%s data_fim_eh_hoje=%s",
        data_inicio, data_fim, data_inicio_ant, data_fim_ant,
        data_fim == date.today(),
    )

    if data_fim == date.today():
        hora_atual = datetime.now().hour
        dominio_anterior = criar_dominio(source, data_inicio_ant, data_fim_ant)
        logger.info("BI hora filter | hora_atual=%s data_fim_ant=%s", hora_atual, data_fim_ant)

        # Filtra hora futura no ano anterior
        for nome, dominio_obj in (("vendas", dominio_anterior.vendas), ("trocas", dominio_anterior.trocas)):
            _debug_items(dominio_obj.items, data_fim_ant, hora_atual, f"ant/{nome}")
            rows_before = len(dominio_obj.items)
            dominio_obj.items = _filtrar_hora(dominio_obj.items, data_fim_ant, hora_atual)
            dominio_obj._df = None  # Invalida cache do DataFrame
            rows_after = len(dominio_obj.items)
            logger.info("BI hora filter | nome=%s rows=%s->%s", nome, rows_before, rows_after)

        # Mesmo filtro de hora futura no domínio atual
        for nome, dominio_obj in (("vendas", dominio_atual.vendas), ("trocas", dominio_atual.trocas)):
            _debug_items(dominio_obj.items, data_fim, hora_atual, f"atual/{nome}")
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
