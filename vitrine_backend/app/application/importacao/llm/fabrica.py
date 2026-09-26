import os

from app.application.importacao.llm.anthropic_provedor import AnthropicProvedor
from app.application.importacao.llm.base import ProvedorLlm
from app.application.importacao.llm.erros import IaIndisponivel
from app.application.importacao.llm.openai_compativel import BASE_URL_OPENAI, OpenAiCompativelProvedor
from app.core.config import settings

PROVEDORES = ("anthropic", "openai")


def _provedor() -> str:
    return settings.ia_provedor.strip().lower()


def _chave_anthropic() -> str:
    return settings.ia_api_key or settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")


def _url_openai() -> str:
    return settings.ia_base_url.strip() or (BASE_URL_OPENAI if settings.ia_api_key else "")


def modelo_efetivo() -> str:
    if settings.ia_modelo:
        return settings.ia_modelo
    return "claude-opus-5" if _provedor() == "anthropic" else ""


def configurado() -> bool:
    if not settings.ia_importacao_habilitada:
        return False
    provedor = _provedor()
    if provedor == "anthropic":
        return bool(_chave_anthropic())
    if provedor == "openai":
        return bool(_url_openai()) and bool(settings.ia_modelo)
    return False


def criar_provedor() -> ProvedorLlm:
    provedor = _provedor()
    if provedor == "anthropic":
        return AnthropicProvedor(modelo=settings.ia_modelo, api_key=_chave_anthropic())
    if provedor == "openai":
        if not _url_openai() or not settings.ia_modelo:
            raise IaIndisponivel("Informe IA_BASE_URL (ou IA_API_KEY) e IA_MODELO para usar a IA compatível com OpenAI.")
        return OpenAiCompativelProvedor(
            modelo=settings.ia_modelo,
            base_url=_url_openai(),
            api_key=settings.ia_api_key,
            modo=settings.ia_modo_json,
            timeout=settings.ia_timeout_segundos,
        )
    raise IaIndisponivel(f"Provedor de IA desconhecido: {settings.ia_provedor!r}. Use um de: {', '.join(PROVEDORES)}.")
