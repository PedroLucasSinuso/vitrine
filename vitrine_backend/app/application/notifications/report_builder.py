from datetime import date, timedelta
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.application.bi.factory import criar_dominio
from app.application.bi.reporting.relatorio import Relatorio
from app.application.bi.schema import Metrica

TEMPLATE_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
TEMPLATE_NAME = "relatorio_semanal.j2"


def _formatar_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def construir_relatorio_semanal(nome_loja: str) -> str:
    hoje = date.today()
    inicio = hoje - timedelta(days=7)
    fim = hoje - timedelta(days=1)

    inicio_ant = inicio - timedelta(days=7)
    fim_ant = inicio - timedelta(days=1)

    dominio = criar_dominio(inicio, fim)
    dominio_ant = criar_dominio(inicio_ant, fim_ant)

    rel = Relatorio(dominio.vendas, dominio.trocas)
    rel_ant = Relatorio(dominio_ant.vendas, dominio_ant.trocas)

    kpis = rel.kpis()
    kpis_ant = rel_ant.kpis()
    ranking = rel.ranking(metrica=Metrica.RECEITA, top=5)

    if kpis_ant.faturamento_bruto and kpis_ant.faturamento_bruto > 0:
        variacao = ((kpis.faturamento_bruto - kpis_ant.faturamento_bruto)
                    / kpis_ant.faturamento_bruto * 100)
        seta = "\u25b2" if variacao >= 0 else "\u25bc"
        variacao_str = f"{seta} {abs(variacao):.1f}%"
        variacao_texto = f"Faturamento: {seta} R$ {abs(kpis.faturamento_bruto - kpis_ant.faturamento_bruto):,.2f} ({abs(variacao):.1f}% {'maior' if variacao >= 0 else 'menor'})"
    else:
        variacao_str = "\u2014"
        variacao_texto = ""

    troca_texto = ""
    if kpis.faturamento_bruto and kpis.faturamento_bruto > 0:
        troca_texto = f"{kpis.total_trocas / kpis.faturamento_bruto * 100:.1f}%"
    else:
        troca_texto = "\u2014"

    template = env.get_template(TEMPLATE_NAME)
    return template.render(
        nome_loja=nome_loja,
        data_inicio=_formatar_data(inicio),
        data_fim=_formatar_data(fim),
        faturamento_bruto=kpis.faturamento_bruto or 0,
        faturamento_liquido=kpis.faturamento_liquido or 0,
        ticket_medio=kpis.ticket_medio or 0,
        qtd_tickets=kpis.qtd_tickets or 0,
        variacao=variacao_str,
        variacao_texto=variacao_texto,
        troca_texto=troca_texto,
        ranking=ranking,
        data_geracao=_formatar_data(hoje),
    )
