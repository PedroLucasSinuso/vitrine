"""
app/application/reporting/pdf/relatorio_semanal_pdf.py

Geração de PDF do relatório semanal.
Usa template HTML próprio (relatorio_pdf.j2) com quebras de página,
tema visual e otimizado para impressão A4 via WeasyPrint.
"""

import logging
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.core.interfaces.source import TransactionSource
from app.application.bi.factory import criar_dominio
from app.application.bi.reporting.relatorio import Relatorio, comparar_kpis
from app.application.bi.schema import Metrica
from app.application.reporting.pdf.pdf_base import html_para_pdf

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
TEMPLATE_NAME = "relatorio_pdf.j2"

_MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def _fmt_money(value: float | None) -> str:
    if value is None:
        return "0,00"
    return f"{value:_.2f}".replace(".", ",").replace("_", ".")


env.filters["fmt_money"] = _fmt_money


def _fmt_variacao(pct: float | None) -> str:
    if pct is None or pct == 0:
        return "\u2014"
    seta = "\u25b2" if pct > 0 else "\u25bc"
    return f"{seta} {abs(pct):.1f}%"


env.filters["fmt_variacao"] = _fmt_variacao


def _formatar_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _formatar_mes(d: date) -> str:
    return f"{_MESES[d.month - 1]} de {d.year}"


def _formatar_mes_ano(d: date) -> str:
    return f"{_MESES[d.month - 1]} {d.year}"


def gerar_relatorio_semanal_pdf(nome_loja: str, source: TransactionSource) -> bytes | None:
    """
    Gera PDF do relatório semanal usando template próprio para impressão.
    Retorna bytes do PDF ou None se WeasyPrint não estiver disponível.
    """
    hoje = date.today()

    inicio_semana = hoje - timedelta(days=7)
    fim_semana = hoje - timedelta(days=1)

    inicio_semana_ant = inicio_semana - timedelta(days=7)
    fim_semana_ant = inicio_semana - timedelta(days=1)

    fim_mes = hoje - timedelta(days=1)
    inicio_mes = fim_mes.replace(day=1)

    dominio_semana = criar_dominio(source, inicio_semana, fim_semana)
    dominio_semana_ant = criar_dominio(source, inicio_semana_ant, fim_semana_ant)
    dominio_mes = criar_dominio(source, inicio_mes, fim_mes)

    rel_semana = Relatorio(dominio_semana.vendas, dominio_semana.trocas)
    rel_semana_ant = Relatorio(dominio_semana_ant.vendas, dominio_semana_ant.trocas)
    rel_mes = Relatorio(dominio_mes.vendas, dominio_mes.trocas)

    kpis_semana = rel_semana.kpis()
    kpis_semana_ant = rel_semana_ant.kpis()
    kpis_mes = rel_mes.kpis()

    ranking_mes = rel_mes.ranking(metrica=Metrica.RECEITA, top=5)

    # Variação da semana
    atual = kpis_semana.faturamento_bruto or 0
    anterior = kpis_semana_ant.faturamento_bruto or 0
    if anterior > 0:
        pct = ((atual - anterior) / anterior) * 100
        if pct == 0:
            variacao_semana = "\u2014"
        else:
            seta = "\u25b2" if pct > 0 else "\u25bc"
            variacao_semana = f"{seta} {abs(pct):.1f}%"
    else:
        variacao_semana = "\u2014"

    # YoY
    try:
        inicio_yoy = inicio_mes.replace(year=inicio_mes.year - 1)
        fim_yoy = fim_mes.replace(year=fim_mes.year - 1)
        dominio_anterior = criar_dominio(source, inicio_yoy, fim_yoy)
        rel_ant = Relatorio(dominio_anterior.vendas, dominio_anterior.trocas)
        kpis_ant = rel_ant.kpis()
        yoy = comparar_kpis(kpis_mes, kpis_ant)
    except Exception as e:
        logger.warning("YoY comparison failed (ERP data may be unavailable for prior year) | erro=%s", e)
        yoy = None

    mes_anterior_data = inicio_mes.replace(year=inicio_mes.year - 1)

    template = env.get_template(TEMPLATE_NAME)
    html = template.render(
        nome_loja=nome_loja,
        data_inicio_semana=_formatar_data(inicio_semana),
        data_fim_semana=_formatar_data(fim_semana),
        data_inicio_mes=_formatar_data(inicio_mes),
        data_fim_mes=_formatar_data(fim_mes),
        mes_atual=_formatar_mes(hoje),
        mes_atual_ref=_formatar_mes_ano(hoje),
        mes_anterior_ref=_formatar_mes_ano(mes_anterior_data),
        faturamento_bruto_semana=kpis_semana.faturamento_bruto or 0,
        faturamento_liquido_semana=kpis_semana.faturamento_liquido or 0,
        ticket_medio_semana=kpis_semana.ticket_medio or 0,
        qtd_tickets_semana=kpis_semana.qtd_tickets or 0,
        faturamento_bruto_mes=kpis_mes.faturamento_bruto or 0,
        faturamento_liquido_mes=kpis_mes.faturamento_liquido or 0,
        ticket_medio_mes=kpis_mes.ticket_medio or 0,
        qtd_tickets_mes=kpis_mes.qtd_tickets or 0,
        variacao_semana=variacao_semana,
        ranking=ranking_mes,
        yoy=yoy,
        data_geracao=_formatar_data(hoje),
    )

    pdf = html_para_pdf(html)
    return pdf
