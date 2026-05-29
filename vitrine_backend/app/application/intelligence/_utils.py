"""Utility helpers for the intelligence module."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Retorna datetime UTC naive (compatível com SQLite que não tem timezone)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_brl(value: float) -> str:
    """Formata valor monetário no padrão pt-BR: R$ 1.234,56

    Python padrao ``:,.2f`` usa formato inglês (1,234.56).
    Esta funcao inverte os separadores para o padrao brasileiro.
    """
    if value is None:
        return "R$ 0,00"
    try:
        formatted = f"{value:,.2f}"            # "1,234.56"
        int_part, dec_part = formatted.split(".")
        int_part = int_part.replace(",", ".")  # "1.234"
        return f"R$ {int_part},{dec_part}"     # "R$ 1.234,56"
    except (ValueError, ZeroDivisionError):
        return "R$ 0,00"
