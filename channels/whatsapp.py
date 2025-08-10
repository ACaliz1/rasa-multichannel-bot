import logging
import asyncio
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from typing import Dict, Text, Any, Callable, Awaitable, Optional
from rasa.core.channels.channel import InputChannel, UserMessage, OutputChannel
import requests

logger = logging.getLogger(__name__)

class WhatsAppOutput(OutputChannel):
    """Canal de salida para WhatsApp Cloud API"""

    @classmethod
    def name(cls) -> Text:
        return "whatsapp"

    def __init__(self, auth_token: Optional[Text], phone_number_id: Optional[Text]) -> None:
        self.auth_token = auth_token
        self.phone_number_id = phone_number_id

    async def send_text_message(self, recipient_id: Text, text: Text, **kwargs: Any) -> None:
        url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text}
        }
        logger.info(f"Enviando mensaje a {recipient_id}: {text}")
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code != 200:
                logger.error(f"Error al enviar mensaje: {resp.status_code} - {resp.text}")
            else:
                logger.info("Mensaje enviado correctamente")
        except Exception as e:
            logger.exception(f"Fallo enviando mensaje a WhatsApp: {e}")


class WhatsAppInput(InputChannel):
    def __init__(self, auth_token: str, phone_number_id: str, verify_token: str):
        self.auth_token = auth_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token

    @classmethod
    def from_credentials(cls, credentials: Dict[str, Any]) -> "WhatsAppInput":
        return cls(
            auth_token=credentials.get("auth_token"),
            phone_number_id=credentials.get("phone_number_id"),
            verify_token=credentials.get("verify_token"),
        )

    def name(self) -> Text:
        return "whatsapp"

    def blueprint(self, on_new_message: Callable[[UserMessage], Awaitable[Any]]) -> Blueprint:
        whatsapp_webhook = Blueprint("whatsapp_webhook", __name__)

        @whatsapp_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @whatsapp_webhook.route("/webhook", methods=["GET"])
        async def verify_token(request: Request) -> HTTPResponse:
            mode = request.args.get("hub.mode")
            token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")

            if mode == "subscribe" and token == self.verify_token:
                logger.info("Webhook verificado correctamente")
                return response.text(challenge)
            logger.error("Fallo en la verificación del Webhook")
            return response.text("Token inválido", status=403)

        @whatsapp_webhook.route("/webhook", methods=["POST"])
        async def message(request: Request) -> HTTPResponse:
            try:
                data = request.json
                logger.debug(f"Datos recibidos: {data}")

                entry = data.get("entry", [])
                if not entry:
                    return response.text("ok", status=200)

                changes = entry[0].get("changes", [])
                if not changes:
                    return response.text("ok", status=200)

                value = changes[0].get("value", {})

                # Mensaje entrante
                if "messages" in value:
                    msg = value["messages"][0]
                    sender = msg.get("from")
                    text_body = msg.get("text", {}).get("body", "")

                    logger.info(f"Mensaje recibido de {sender}: {text_body}")

                    out_channel = WhatsAppOutput(self.auth_token, self.phone_number_id)

                    async def process():
                        try:
                            await on_new_message(
                                UserMessage(
                                    text=text_body,
                                    output_channel=out_channel,
                                    sender_id=sender,
                                    input_channel=self.name(),
                                    metadata=data
                                )
                            )
                        except Exception as e:
                            logger.exception(f"Error en procesamiento async: {e}")

                    # Procesa en background para no bloquear el webhook
                    asyncio.create_task(process())

                # Estados (entregado, leído, etc.)
                elif "statuses" in value:
                    st = value["statuses"][0]
                    logger.info(f"Status recibido: {st.get('status')} para ID {st.get('id')}")

                # Responder rápido siempre
                return response.text("ok", status=200)

            except Exception as e:
                logger.exception(f"Error al procesar mensaje: {e}")
                return response.text("error", status=500)

        return whatsapp_webhook
