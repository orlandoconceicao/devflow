import json
from urllib.request import Request, urlopen

from django.conf import settings


class MessagingNotConfigured(Exception):
    pass


def send_whatsapp(*, phone, message):
    if settings.MESSAGE_PROVIDER != "meta_whatsapp":
        raise MessagingNotConfigured("Configure MESSAGE_PROVIDER=meta_whatsapp.")
    if not settings.WHATSAPP_API_URL or not settings.WHATSAPP_ACCESS_TOKEN:
        raise MessagingNotConfigured("Configure a API e o token do WhatsApp.")
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": message},
        }
    ).encode()
    request = Request(
        settings.WHATSAPP_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        return 200 <= response.status < 300
