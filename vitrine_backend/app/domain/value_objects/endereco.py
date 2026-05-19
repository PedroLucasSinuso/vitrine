"""Value Object Endereco.

Encapsula os dados de endereço do estabelecimento com validação,
formatação humano/IA e preparação para enriquecimento futuro
(IBGE, coordenadas, dados demográficos).
"""

import re
from typing import Optional
from pydantic import BaseModel, field_validator


_UFS_VALIDAS: set[str] = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

_RE_CEP = re.compile(r"^\d{5}-?\d{3}$")


def validar_cep(valor: str) -> str:
    """Valida e normaliza CEP. Retorna 8 dígitos sem máscara."""
    if not _RE_CEP.match(valor.strip()):
        raise ValueError(
            f"CEP inválido: {valor!r}. Use o formato 01001000 ou 01001-000."
        )
    return valor.strip().replace("-", "")


def validar_uf(valor: str) -> str:
    """Valida e normaliza UF. Retorna sigla em maiúsculo."""
    uf = valor.strip().upper()
    if uf not in _UFS_VALIDAS:
        raise ValueError(
            f"UF inválida: {valor!r}. Use uma sigla de 2 letras (SP, RJ, MG, ...)."
        )
    return uf


def formatar_cep(cep: str) -> str:
    """Formata CEP de 8 dígitos para 01001-000."""
    if len(cep) == 8 and cep.isdigit():
        return f"{cep[:5]}-{cep[5:]}"
    return cep


class Endereco(BaseModel):
    """Value Object para dados de endereço do estabelecimento.

    Nível 1 — campos preenchidos pelo ConfigService (configurados na UI):
        rua, numero, complemento, bairro, cidade, estado, cep

    Nível 2 — campos enriquecidos por API externa (ViaCEP, BrasilAPI),
        opcionais, preparados para consumo futuro pela IA.

    Nível 3 (futuro, comentado) — dados demográficos censitários:
        idh, renda_media, densidade_populacional, etc.
    """

    # ── Nível 1: ConfigService ──────────────────────────────────────────
    rua: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    cidade: str = ""
    estado: str = ""
    cep: str = ""

    # ── Nível 2: Enriquecido por API externa ────────────────────────────
    codigo_ibge: Optional[str] = None
    ddd: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # ── Nível 3: Dados demográficos (sob demanda, futuros) ──────────────
    # idh: Optional[float] = None
    # renda_media: Optional[float] = None
    # densidade_populacional: Optional[float] = None
    # urbanizacao: Optional[float] = None

    # ── Validators ──────────────────────────────────────────────────────

    @field_validator("cep")
    @classmethod
    def _validar_cep(cls, v: str) -> str:
        if not v:
            return v
        return validar_cep(v)

    @field_validator("estado")
    @classmethod
    def _validar_uf(cls, v: str) -> str:
        if not v:
            return v
        return validar_uf(v)

    # ── Propriedades de formatação ──────────────────────────────────────

    @property
    def cep_formatado(self) -> str:
        """CEP no formato 01001-000."""
        return formatar_cep(self.cep) if self.cep else ""

    @property
    def formatado(self) -> str:
        """String legível para humanos (exibição na UI, relatórios)."""
        parts = []
        linha1 = self.rua
        if self.numero:
            linha1 += f", {self.numero}"
        if self.complemento:
            linha1 += f" — {self.complemento}"
        parts.append(linha1)

        linha2 = self.bairro
        if self.cidade:
            linha2 += f", {self.cidade}"
        if self.estado:
            linha2 += f" - {self.estado}"
        parts.append(linha2)

        if self.cep:
            parts.append(f"CEP {self.cep_formatado}")

        return " | ".join(p for p in parts if p)

    @property
    def completo(self) -> bool:
        """Retorna True se todos os campos obrigatórios estão preenchidos."""
        return all([self.rua, self.numero, self.bairro, self.cidade, self.estado, self.cep])

    # ── Saída otimizada pra IA ──────────────────────────────────────────

    def para_prompt_ia(self) -> str:
        """Bloco estruturado para alimentar schemas de prompt de IA.

        Usa labels claros e sem ambiguidade, ideal para extração por LLM
        ou montagem de contexto enriquecido.
        """
        return (
            f"LOGRADOURO: {self.rua}\n"
            f"NUMERO: {self.numero}\n"
            f"COMPLEMENTO: {self.complemento or '(vazio)'}\n"
            f"BAIRRO: {self.bairro}\n"
            f"CIDADE: {self.cidade}\n"
            f"ESTADO: {self.estado}\n"
            f"CEP: {self.cep_formatado or '(vazio)'}\n"
            f"IBGE: {self.codigo_ibge or '(não informado)'}\n"
            f"DDD: {self.ddd or '(não informado)'}\n"
            f"LAT: {self.latitude if self.latitude is not None else '(não informado)'}\n"
            f"LNG: {self.longitude if self.longitude is not None else '(não informado)'}"
        )

    def para_json_ia(self) -> dict:
        """Dicionário limpo para consumo da IA via tool call."""
        return self.model_dump(exclude_none=True)

    # ── Factory ─────────────────────────────────────────────────────────

    @classmethod
    def from_config_service(cls, db) -> "Endereco":
        """Constrói um Endereco lendo as 7 chaves do ConfigService.

        Útil para módulos consumidores (IA, relatórios) que precisam
        do endereço sem se preocupar com a origem dos dados.
        """
        from app.application.config_service import get

        return cls(
            rua=get(db, "endereco_rua"),
            numero=get(db, "endereco_numero"),
            complemento=get(db, "endereco_complemento"),
            bairro=get(db, "endereco_bairro"),
            cidade=get(db, "endereco_cidade"),
            estado=get(db, "endereco_estado"),
            cep=get(db, "endereco_cep"),
        )
