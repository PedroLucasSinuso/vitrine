import hashlib
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.application.importacao.extracao import Celula

FORMATOS_DATA = {
    "dd/mm/aaaa": ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d.%m.%Y"),
    "aaaa-mm-dd": ("%Y-%m-%d", "%Y/%m/%d"),
    "mm/dd/aaaa": ("%m/%d/%Y", "%m/%d/%y"),
}
_DATA_BR = re.compile(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})")


def normalizar_texto(valor: Celula) -> str:
    if valor is None:
        return ""
    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    texto = re.sub(r"\d+", "#", texto.lower())
    return re.sub(r"[^a-z#%]+", " ", texto).strip()


def assinatura_linha(linha: list[Celula]) -> str | None:
    tokens = [normalizar_texto(c) for c in linha if isinstance(c, str) and normalizar_texto(c)]
    if len(tokens) < 2:
        return None
    return hashlib.sha256("|".join(tokens).encode()).hexdigest()


def texto(valor: Celula) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    resultado = str(valor).strip()
    return resultado or None


def numero(valor: Celula, separador_decimal: str = ",") -> Decimal | None:
    if valor is None or isinstance(valor, (date, datetime)):
        return None
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return Decimal(str(valor))
    bruto = str(valor).strip()
    if not bruto or bruto in ("-", "—"):
        return None
    negativo = bruto.startswith("(") and bruto.endswith(")") or bruto.startswith("-") or bruto.endswith("-")
    limpo = re.sub(r"[^\d,.]", "", bruto)
    if not limpo:
        return None
    if separador_decimal == ",":
        limpo = limpo.replace(".", "").replace(",", ".")
    else:
        limpo = limpo.replace(",", "")
    try:
        resultado = Decimal(limpo)
    except InvalidOperation:
        return None
    return -resultado if negativo else resultado


def inteiro(valor: Celula, separador_decimal: str = ",") -> int | None:
    resultado = numero(valor, separador_decimal)
    if resultado is None or resultado != resultado.to_integral_value():
        return None
    return int(resultado)


def data(valor: Celula, formato: str = "dd/mm/aaaa") -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if valor is None:
        return None
    bruto = str(valor).strip().split(" ")[0]
    for padrao in FORMATOS_DATA.get(formato, ()):
        try:
            return datetime.strptime(bruto, padrao).date()
        except ValueError:
            continue
    return None


def datas_no_texto(valor: Celula) -> list[date]:
    encontradas = []
    for dia, mes, ano in _DATA_BR.findall(str(valor or "")):
        ano_int = int(ano) + 2000 if len(ano) == 2 else int(ano)
        try:
            encontradas.append(date(ano_int, int(mes), int(dia)))
        except ValueError:
            continue
    return encontradas
