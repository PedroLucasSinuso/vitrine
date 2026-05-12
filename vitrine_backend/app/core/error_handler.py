import logging

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_PUBLICA = "Erro interno ao processar a operacao. Tente novamente mais tarde."

MENSAGENS_ERRO_PUBLICAS: dict[type, str] = {
    ValueError: "Dados invalidos fornecidos.",
    PermissionError: "Sem permissao para realizar esta operacao.",
    TimeoutError: "A operacao excedeu o tempo limite. Tente novamente.",
    ConnectionError: "Nao foi possivel conectar ao servidor. Tente novamente.",
}


def sanitizar_erro(erro: Exception) -> str:
    erro_type = type(erro)
    for tipo, mensagem in MENSAGENS_ERRO_PUBLICAS.items():
        if issubclass(erro_type, tipo):
            return mensagem
    return MENSAGEM_ERRO_PUBLICA


def logar_erro_interno(mensagem: str, erro: Exception):
    logger.exception("%s | Erro interno: %s", mensagem, erro)
