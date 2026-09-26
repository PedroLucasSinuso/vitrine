import logging

from app.application.importacao.llm.erros import IaIndisponivel

logger = logging.getLogger(__name__)

BETA_FALLBACK = "server-side-fallback-2026-07-01"
MODELO_PADRAO = "claude-opus-5"


class AnthropicProvedor:
    nome = "anthropic"

    def __init__(self, modelo: str = "", api_key: str = "", cliente=None):
        self.modelo = modelo or MODELO_PADRAO
        self._api_key = api_key
        self._cliente = cliente

    def _obter_cliente(self):
        if self._cliente is None:
            import anthropic

            self._cliente = anthropic.Anthropic(api_key=self._api_key or None)
        return self._cliente

    def gerar_json(self, sistema: str, usuario: str, esquema: dict) -> str:
        import anthropic

        try:
            resposta = self._obter_cliente().beta.messages.create(
                model=self.modelo,
                max_tokens=16000,
                betas=[BETA_FALLBACK],
                fallbacks="default",
                system=sistema,
                messages=[{"role": "user", "content": usuario}],
                output_config={"format": {"type": "json_schema", "schema": esquema}},
            )
        except anthropic.APIConnectionError as erro:
            raise IaIndisponivel("Sem conexão com o serviço de IA.") from erro
        except anthropic.RateLimitError as erro:
            raise IaIndisponivel("Serviço de IA ocupado no momento.") from erro
        except anthropic.APIStatusError as erro:
            logger.error("IA importação falhou | provedor=anthropic status=%s", erro.status_code)
            raise IaIndisponivel("O serviço de IA recusou o pedido.") from erro

        if resposta.stop_reason == "refusal":
            raise IaIndisponivel("A IA não conseguiu analisar este arquivo.")
        if resposta.stop_reason == "max_tokens":
            raise IaIndisponivel("A resposta da IA veio incompleta.")
        texto = next((b.text for b in resposta.content if b.type == "text"), None)
        if texto is None:
            raise IaIndisponivel("A IA não devolveu uma sugestão.")
        return texto
