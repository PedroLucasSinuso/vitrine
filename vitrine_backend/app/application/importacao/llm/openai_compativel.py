import json
import logging

import httpx

from app.application.importacao.llm.erros import IaIndisponivel, RespostaInvalida

logger = logging.getLogger(__name__)

MODOS = ("json_schema", "json_object", "prompt")
BASE_URL_OPENAI = "https://api.openai.com/v1"
MAX_TOKENS = 2048
TRECHO_DO_ERRO = 300

_MODO_QUE_FUNCIONOU: dict[tuple[str, str], str] = {}


class _ModoNaoSuportado(Exception):
    pass


def esquecer_modos_aprendidos() -> None:
    _MODO_QUE_FUNCIONOU.clear()


class OpenAiCompativelProvedor:
    nome = "openai"

    def __init__(
        self,
        modelo: str,
        base_url: str = BASE_URL_OPENAI,
        api_key: str = "",
        modo: str = "auto",
        timeout: float = 90.0,
        cliente_http: httpx.Client | None = None,
    ):
        if modo != "auto" and modo not in MODOS:
            raise ValueError(f"Modo JSON desconhecido: {modo}")
        self.modelo = modelo
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._api_key = api_key
        self._modo = modo
        self._timeout = timeout
        self._cliente_http = cliente_http

    def _cabecalhos(self) -> dict[str, str]:
        cabecalhos = {"Content-Type": "application/json"}
        if self._api_key:
            cabecalhos["Authorization"] = f"Bearer {self._api_key}"
        return cabecalhos

    def _corpo(self, modo: str, sistema: str, usuario: str, esquema: dict) -> dict:
        instrucao_de_formato = (
            "\n\nResponda SOMENTE com um objeto JSON válido, sem texto antes ou depois e sem "
            f"blocos de código, seguindo este JSON Schema:\n{json.dumps(esquema, ensure_ascii=False)}"
        )
        corpo = {
            "model": self.modelo,
            "temperature": 0,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": sistema if modo == "json_schema" else sistema + instrucao_de_formato},
                {"role": "user", "content": usuario},
            ],
        }
        if modo == "json_schema":
            corpo["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "mapeamento", "schema": esquema, "strict": True},
            }
        elif modo == "json_object":
            corpo["response_format"] = {"type": "json_object"}
        return corpo

    def _ordem_dos_modos(self) -> list[str]:
        if self._modo != "auto":
            return [self._modo]
        aprendido = _MODO_QUE_FUNCIONOU.get((self._url, self.modelo))
        return [aprendido] if aprendido else list(MODOS)

    def gerar_json(self, sistema: str, usuario: str, esquema: dict) -> str:
        for modo in self._ordem_dos_modos():
            try:
                texto = self._pedir(modo, sistema, usuario, esquema)
            except _ModoNaoSuportado:
                logger.warning("Provedor recusou o modo %s; tentando o próximo | modelo=%s", modo, self.modelo)
                continue
            if self._modo == "auto":
                _MODO_QUE_FUNCIONOU[(self._url, self.modelo)] = modo
            return texto
        if self._modo == "auto" and (self._url, self.modelo) in _MODO_QUE_FUNCIONOU:
            del _MODO_QUE_FUNCIONOU[(self._url, self.modelo)]
        raise IaIndisponivel("O serviço de IA recusou o pedido. Confira o modelo e o endereço configurados.")

    def _pedir(self, modo: str, sistema: str, usuario: str, esquema: dict) -> str:
        cliente = self._cliente_http or httpx.Client(timeout=self._timeout)
        try:
            resposta = cliente.post(self._url, headers=self._cabecalhos(), json=self._corpo(modo, sistema, usuario, esquema))
        except httpx.TransportError as erro:
            raise IaIndisponivel("Sem conexão com o serviço de IA.") from erro
        finally:
            if self._cliente_http is None:
                cliente.close()

        status = resposta.status_code
        if status in (400, 422):
            logger.warning("IA importação | modo=%s status=%s corpo=%s", modo, status, resposta.text[:TRECHO_DO_ERRO])
            raise _ModoNaoSuportado()
        if status in (401, 403):
            raise IaIndisponivel("A credencial do serviço de IA foi recusada.")
        if status == 429:
            raise IaIndisponivel("Serviço de IA ocupado no momento.")
        if status >= 400:
            logger.error("IA importação falhou | status=%s corpo=%s", status, resposta.text[:TRECHO_DO_ERRO])
            raise IaIndisponivel("O serviço de IA está indisponível." if status >= 500 else "O serviço de IA recusou o pedido.")
        return self._extrair_texto(resposta)

    @staticmethod
    def _extrair_texto(resposta: httpx.Response) -> str:
        try:
            escolha = resposta.json()["choices"][0]
            conteudo = escolha["message"]["content"]
            motivo = escolha.get("finish_reason")
        except (ValueError, KeyError, IndexError, TypeError) as erro:
            raise RespostaInvalida("O serviço de IA respondeu num formato inesperado.") from erro
        if motivo == "length":
            raise IaIndisponivel("A resposta da IA veio incompleta.")
        if motivo == "content_filter":
            raise IaIndisponivel("A IA não conseguiu analisar este arquivo.")
        if isinstance(conteudo, list):
            conteudo = "".join(parte.get("text", "") for parte in conteudo if isinstance(parte, dict))
        if not isinstance(conteudo, str) or not conteudo.strip():
            raise RespostaInvalida("A IA devolveu uma resposta vazia.")
        return conteudo
