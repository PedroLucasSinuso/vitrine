"""Geração de EAN-13 válido.

Os códigos de barras da demo precisam passar pela mesma validação de
dígito verificador que os reais (``app/domain/value_objects/codigo.py``) —
senão a busca por código e as telas de SKU respondem 400.
"""

# Prefixo GS1 do Brasil. Não identifica nenhuma empresa real: os 9 dígitos
# seguintes são um sequencial da demo, não um registro GS1.
PREFIXO_BR = "789"


def digito_verificador(corpo: str) -> int:
    """Calcula o 13º dígito de um EAN a partir dos 12 primeiros.

    Mesma conta de ``Codigo._validar_ean``, ao contrário: pesos 3 e 1
    alternados da direita para a esquerda.
    """
    soma = 0
    peso = 3
    for ch in reversed(corpo):
        soma += int(ch) * peso
        peso = 1 if peso == 3 else 3
    return (10 - (soma % 10)) % 10


def gerar_ean13(sequencial: int) -> str:
    """EAN-13 determinístico para o n-ésimo código da demo."""
    corpo = f"{PREFIXO_BR}{sequencial:09d}"
    return f"{corpo}{digito_verificador(corpo)}"
