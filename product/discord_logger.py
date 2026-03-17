import requests
from django.conf import settings

def enviar_discord(mensaje, color=5763719):

    webhook = settings.DISCORD_WEBHOOK_URL

    data = {
        "embeds": [
            {
                "description": mensaje,
                "color": color
            }
        ]
    }

    try:
        requests.post(webhook, json=data, timeout=3)
    except:
        pass