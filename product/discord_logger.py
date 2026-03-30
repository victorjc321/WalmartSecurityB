import requests
from django.conf import settings


def enviar_discord(mensaje, color=5763719, request=None):

    webhook = settings.DISCORD_WEBHOOK_URL

    ip = request.META.get("REMOTE_ADDR") if request else "N/A"
    user_agent = request.META.get("HTTP_USER_AGENT") if request else "N/A"
    user = request.user if request and request.user.is_authenticated else "Anon"

    data = {
        "embeds": [
            {
                "title": "🔐 Seguridad del sistema",
                "description": mensaje,
                "color": color,
                "fields": [
                    {"name": "👤 Usuario", "value": str(user), "inline": True},
                    {"name": "🌐 IP", "value": ip, "inline": True},
                    {
                        "name": "💻 User-Agent",
                        "value": user_agent[:1000],
                        "inline": False,
                    },
                ],
            }
        ]
    }

    try:
        requests.post(webhook, json=data, timeout=3)
    except:
        pass
