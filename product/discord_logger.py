import requests
from django.conf import settings


def enviar_discord(mensaje, color=5763719, request=None, include_meta=False):

    webhook = settings.DISCORD_WEBHOOK_URL

    embed = {"description": mensaje, "color": color}

    if include_meta and request:
        ip = request.META.get("REMOTE_ADDR", "N/A")
        user_agent = request.META.get("HTTP_USER_AGENT", "N/A")
        user = request.user if request.user.is_authenticated else "Anon"

        embed["fields"] = [
            {"name": "👤 Usuario", "value": str(user), "inline": True},
            {"name": "🌐 IP", "value": ip, "inline": True},
            {"name": "💻 User-Agent", "value": user_agent[:500], "inline": False},
        ]

    data = {"embeds": [embed]}

    try:
        requests.post(webhook, json=data, timeout=3)
    except:
        pass
