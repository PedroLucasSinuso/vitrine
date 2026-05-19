"""Serviço de enriquecimento de Endereco via API externa (ViaCEP / BrasilAPI).

Uso futuro: ao salvar o CEP, chamar este serviço para preencher
automaticamente código IBGE, DDD e coordenadas no Value Object.

Independe do ConfigService — recebe e retorna um Endereco.
"""

import logging
from typing import Optional
from app.domain.value_objects.endereco import Endereco

logger = logging.getLogger(__name__)


def enriquecer_por_cep(endereco: Endereco) -> Endereco:
    """Busca dados complementares (IBGE, DDD, coordenadas) a partir do CEP.

    Usa a BrasilAPI (https://brasilapi.com.br/api/cep/v1/{cep}) como fonte
    primária, com fallback para ViaCEP.

    Retorna o mesmo Endereco com os campos de Nível 2 preenchidos.
    Se a API falhar ou o CEP não for encontrado, retorna o objeto original.
    """
    cep = endereco.cep
    if not cep or len(cep) != 8 or not cep.isdigit():
        return endereco

    dados = _buscar_brasilapi(cep) or _buscar_viacep(cep)
    if not dados:
        return endereco

    return endereco.model_copy(update={
        "codigo_ibge": dados.get("ibge"),
        "ddd": dados.get("ddd"),
        "latitude": dados.get("latitude"),
        "longitude": dados.get("longitude"),
    })


def _buscar_brasilapi(cep: str) -> Optional[dict]:
    """Tenta enriquecer via BrasilAPI (recomendada)."""
    try:
        import httpx
        resp = httpx.get(f"https://brasilapi.com.br/api/cep/v1/{cep}", timeout=5)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "ibge": data.get("ibge"),
            "ddd": data.get("ddd"),
            "latitude": _parse_float(data.get("latitude")),
            "longitude": _parse_float(data.get("longitude")),
        }
    except Exception as e:
        logger.debug("BrasilAPI falhou para CEP %s: %s", cep, e)
        return None


def _buscar_viacep(cep: str) -> Optional[dict]:
    """Fallback para ViaCEP."""
    try:
        import httpx
        cep_fmt = f"{cep[:5]}-{cep[5:]}"
        resp = httpx.get(f"https://viacep.com.br/ws/{cep_fmt}/json/", timeout=5)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("erro"):
            return None
        return {
            "ibge": data.get("ibge"),
            "ddd": data.get("ddd"),
            "latitude": None,  # ViaCEP não retorna coordenadas
            "longitude": None,
        }
    except Exception as e:
        logger.debug("ViaCEP falhou para CEP %s: %s", cep, e)
        return None


def _parse_float(valor) -> Optional[float]:
    if valor is None:
        return None
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None
