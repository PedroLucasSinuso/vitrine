import logging
from twilio.rest import Client
from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    def __init__(self):
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.from_number = f"whatsapp:{settings.twilio_from_number}"

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
