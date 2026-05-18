import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self, sid: str, token: str, from_number: str):
        self.client = Client(sid, token)
        self.from_number = f"whatsapp:{from_number}" if from_number else ""

    def enviar_texto(self, numero: str, mensagem: str) -> bool:
        try:
            msg = self.client.messages.create(
                body=mensagem,
                from_=self.from_number,
                to=f"whatsapp:{numero}",
            )
            logger.info("WhatsApp enviado | numero=%s sid=%s", numero, msg.sid)
            return msg.error_code is None
        except Exception as e:
            logger.error("Erro ao enviar WhatsApp | numero=%s erro=%s", numero, e)
            return False

    def enviar_para_lista(self, numeros: list[str], mensagem: str) -> dict[str, bool]:
        resultados: dict[str, bool] = {}
        for numero in numeros:
            resultados[numero] = self.enviar_texto(numero, mensagem)
        return resultados
