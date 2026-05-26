import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from twilio.rest import Client

_MAX_WORKERS = 4

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
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            futuros = {executor.submit(self.enviar_texto, num, mensagem): num for num in numeros}
            for fut in as_completed(futuros):
                numero = futuros[fut]
                try:
                    resultados[numero] = fut.result()
                except Exception as e:
                    logger.error("Erro inesperado no WhatsApp paralelo | numero=%s erro=%s", numero, e)
                    resultados[numero] = False
        return resultados
