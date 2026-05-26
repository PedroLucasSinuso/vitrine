"""
app/application/reporting/pdf/pdf_base.py

Geração de PDF usando WeasyPrint.
Fallback natural: se WeasyPrint não estiver disponível (GTK ausente no Windows),
a função retorna None e o frontend usa window.print() como fallback.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Tenta importar WeasyPrint — falha silenciosa no Windows sem GTK
_HAS_WEASYPRINT = False
try:
    from weasyprint import HTML as _WeasyHTML
    _HAS_WEASYPRINT = True
except (ImportError, OSError) as e:
    logger.info("WeasyPrint não disponível (esperado no Windows sem GTK). Usando fallback frontend. | detalhe=%s", e)


def html_para_pdf(html: str, base_url: str | Path | None = None) -> bytes | None:
    """
    Converte HTML em PDF via WeasyPrint.

    Retorna bytes do PDF, ou None se WeasyPrint não estiver disponível.
    O frontend deve usar window.print() como fallback.
    """
    if not _HAS_WEASYPRINT:
        logger.debug("WeasyPrint indisponível — pulando geração de PDF")
        return None

    try:
        pdf_bytes = _WeasyHTML(string=html, base_url=base_url).write_pdf()
        logger.info("PDF gerado | tamanho=%d bytes", len(pdf_bytes))
        return pdf_bytes
    except Exception as e:
        logger.error("Erro ao gerar PDF | erro=%s", e)
        return None
