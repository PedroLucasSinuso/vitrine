import logging
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)
from app.core.interfaces.source import TransactionSource
from app.application.bi.factory import criar_dominio
from app.application.bi.reporting.relatorio import Relatorio, comparar_kpis
from app.application.bi.schema import Metrica

TEMPLATE_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
TEMPLATE_NAME = "relatorio_email.j2"

STATIC_DIR = Path(__file__).parent.parent.parent / "static"

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
        return "—"
    seta = "▲" if pct > 0 else "▼"
    return f"{seta} {abs(pct):.1f}%"


env.filters["fmt_variacao"] = _fmt_variacao


def _formatar_data(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _formatar_mes(d: date) -> str:
    return f"{_MESES[d.month - 1]} de {d.year}"


def _formatar_mes_ano(d: date) -> str:
    return f"{_MESES[d.month - 1]} {d.year}"


def _cid_nome_arquivo(path: Path) -> tuple[str, str]:
    """Retorna (cid_name, mime_type) baseado na extensão."""
    ext = path.suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".gif": "image/gif", ".svg": "image/svg+xml"}
    mime = mime_map.get(ext, "image/png")
    return f"img{hash(str(path)) & 0x7FFFFFFF}", mime


def _carregar_imagens() -> list[tuple[str, bytes, str]]:
    """Carrega as imagens estáticas e retorna [(cid, bytes, mimetype), ...]."""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    imagens = []
    logo_paths = sorted(STATIC_DIR.glob("logo.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if logo_paths:
        path = logo_paths[0]
        cid, mime = _cid_nome_arquivo(path)
        imagens.append((cid, path.read_bytes(), mime))
    vitrine_paths = sorted(STATIC_DIR.glob("vitrine_logo.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if vitrine_paths:
        path = vitrine_paths[0]
        cid, mime = _cid_nome_arquivo(path)
        imagens.append((cid, path.read_bytes(), mime))
    return imagens


def construir_relatorio_email(nome_loja: str, source: TransactionSource) -> tuple[str, list[tuple[str, bytes, str]], bytes | None]:
    """Retorna (html, imagens_cid, anexo_xlsx_bytes). O anexo pode ser None se não houver dados."""
    from app.application.bi.reporting.exportador import build_bi_anexo

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

    # Gera .xlsx com os mesmos dados (anexo)
    anexo_bytes = build_bi_anexo(
        kpis_semana=kpis_semana.model_dump(),
        kpis_mes=kpis_mes.model_dump(),
        ranking=[r.model_dump() for r in ranking_mes],
    )

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

    imagens = _carregar_imagens()
    cid_logo = imagens[0][0] if len(imagens) > 0 else ""
    cid_vitrine = imagens[1][0] if len(imagens) > 1 else ""
    mes_anterior_data = inicio_mes.replace(year=inicio_mes.year - 1)

    variacao_semana = _calcular_variacao_str(kpis_semana.faturamento_bruto, kpis_semana_ant.faturamento_bruto)

    template = env.get_template(TEMPLATE_NAME)
    html = template.render(
        nome_loja=nome_loja,
        logo_cid=cid_logo,
        vitrine_logo_cid=cid_vitrine,
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

    return html, imagens, anexo_bytes


def _calcular_variacao_str(atual: float, anterior: float) -> str:
    if anterior and anterior > 0:
        pct = ((atual - anterior) / anterior) * 100
        if pct == 0:
            return "—"
        seta = "▲" if pct > 0 else "▼"
        return f"{seta} {abs(pct):.1f}%"
    return "—"
