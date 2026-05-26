"""
app/application/reporting/pdf/relatorio_semanal_pdf.py

Geração de PDF do relatório semanal.
Reaproveita o template HTML do email (relatorio_email.j2) via WeasyPrint.
"""

import logging
from datetime import date
from pathlib import Path

from app.application.notifications.report_builder_email import construir_relatorio_email
from app.application.reporting.pdf.pdf_base import html_para_pdf
from app.core.interfaces.source import TransactionSource

logger = logging.getLogger(__name__)


def gerar_relatorio_semanal_pdf(nome_loja: str, source: TransactionSource) -> bytes | None:
    """
    Gera PDF do relatório semanal.

    Reaproveita a função construir_relatorio_email() para obter o HTML,
    depois converte para PDF via WeasyPrint.

    Retorna bytes do PDF ou None se WeasyPrint não estiver disponível.
    """
    html, _imagens, _anexo = construir_relatorio_email(nome_loja, source)

    # Base URL para resolver imagens (cid: não funciona no PDF — WeasyPrint
    # precisa de URL real ou caminho de arquivo). Logo não será incluída no PDF
    # a menos que sejam usados caminhos absolutos.
    static_dir = Path(__file__).parent.parent.parent / "static"

    pdf = html_para_pdf(html, base_url=str(static_dir) if static_dir.exists() else None)
    return pdf
