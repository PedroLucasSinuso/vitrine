from typing import Protocol


class ProvedorLlm(Protocol):
    nome: str
    modelo: str

    def gerar_json(self, sistema: str, usuario: str, esquema: dict) -> str: ...
