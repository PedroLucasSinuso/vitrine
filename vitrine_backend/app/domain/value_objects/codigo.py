import re
from typing import Optional


class Codigo:
    def __init__(self, valor: str) -> None:
        """Inicializa o código validando o valor e detectando seu tipo (EAN, PLU)."""
        if not isinstance(valor, str):
            raise TypeError("Codigo deve ser uma string")
        normalizado = self.normalizar(valor)
        if not self.validar(normalizado):
            raise ValueError(f"Codigo invalido: {valor!r}")
        self._valor = normalizado
        self._tipo = self.detectar_tipo(normalizado)

    @property
    def valor(self) -> str:
        return self._valor

    @property
    def tipo(self) -> Optional[str]:
        return self._tipo

    @staticmethod
    def normalizar(codigo: str) -> str:
        """Remove espaços e traços, faz zero-padding e retorna o código limpo."""
        codigo = codigo.strip()
        codigo = re.sub(r"[\s-]", "", codigo)
        if codigo.isdigit() and 1 <= len(codigo) <= 6:
            codigo = codigo.zfill(6)
        return codigo

    @classmethod
    def validar(cls, codigo: str) -> bool:
        """Valida se o código é de algum tipo suportado (EAN ou PLU)."""
        return cls.detectar_tipo(codigo) is not None

    @classmethod
    def detectar_tipo(cls, codigo: str) -> Optional[str]:
        """Identifica o tipo do código: EAN13, EAN12, EAN8 ou PLU6."""
        if cls.is_ean13(codigo):
            return "EAN13"
        if cls.is_ean12(codigo):
            return "EAN12"
        if cls.is_ean8(codigo):
            return "EAN8"
        if cls.is_plu6(codigo):
            return "PLU6"
        return None

    @classmethod
    def is_ean13(cls, codigo: str) -> bool:
        """Verifica se o código é um EAN-13 válido."""
        return cls._validar_ean(codigo, 13)

    @classmethod
    def is_ean12(cls, codigo: str) -> bool:
        """Verifica se o código é um EAN-12 válido."""
        return cls._validar_ean(codigo, 12)

    @classmethod
    def is_ean8(cls, codigo: str) -> bool:
        """Verifica se o código é um EAN-8 válido."""
        return cls._validar_ean(codigo, 8)

    @staticmethod
    def is_plu6(codigo: str) -> bool:
        """Verifica se o código é um PLU de 6 dígitos válido."""
        return codigo.isdigit() and 1 <= len(codigo) <= 6

    @staticmethod
    def _validar_ean(codigo: str, tamanho: int) -> bool:
        """Valida um código EAN usando o algoritmo de dígito verificador."""
        if len(codigo) != tamanho or not codigo.isdigit():
            return False
        corpo = codigo[:-1]
        digito = int(codigo[-1])
        soma = 0
        peso = 3
        for ch in reversed(corpo):
            soma += int(ch) * peso
            peso = 1 if peso == 3 else 3
        calculado = (10 - (soma % 10)) % 10
        return calculado == digito

    def __repr__(self):
        return f"Codigo({self._valor})"

    def __eq__(self, other):
        if isinstance(other, Codigo):
            return self.valor == other.valor
        return False