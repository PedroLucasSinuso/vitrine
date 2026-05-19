"""Schemas de API para Endereco.

Camada fina — apenas valida os campos que chegam no PATCH.
A validação pesada (CEP, UF) delega para as funções do Value Object.
"""

from pydantic import BaseModel, field_validator
from app.domain.value_objects.endereco import validar_cep, validar_uf


_CHAVES_ENDERECO = {
    "endereco_rua",
    "endereco_numero",
    "endereco_complemento",
    "endereco_bairro",
    "endereco_cidade",
    "endereco_estado",
    "endereco_cep",
}


class EnderecoUpdate(BaseModel):
    """Valida os campos de endereço enviados no PATCH /admin/configuracoes."""

    endereco_rua: str | None = None
    endereco_numero: str | None = None
    endereco_complemento: str | None = None
    endereco_bairro: str | None = None
    endereco_cidade: str | None = None
    endereco_estado: str | None = None
    endereco_cep: str | None = None

    @field_validator("endereco_cep")
    @classmethod
    def validar_cep(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return v
        return validar_cep(v)

    @field_validator("endereco_estado")
    @classmethod
    def validar_uf(cls, v: str | None) -> str | None:
        if v is None or not v.strip():
            return v
        return validar_uf(v)


def extrair_endereco_update(valores: dict[str, str]) -> dict[str, str]:
    """Extrai e valida apenas os campos de endereço de um dicionário genérico.

    Útil para validar os campos de endereço dentro do PATCH geral,
    sem precisar mudar o schema ConfiguracaoUpdate.
    """
    endereco_data = {k: v for k, v in valores.items() if k in _CHAVES_ENDERECO}
    if not endereco_data:
        return {}
    # Valida usando o schema (lança ValidationError se inválido)
    validated = EnderecoUpdate(**endereco_data)
    return validated.model_dump(exclude_none=True)
