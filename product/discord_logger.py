import requests
from django.conf import settings


def get_client_ip(request):
    cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
    if cf_ip:
        return cf_ip

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def enviar_discord(mensaje, color=5763719, request=None, include_meta=False):

    webhook = settings.DISCORD_WEBHOOK_URL

    embed = {"description": mensaje, "color": color}

    if include_meta and request:
        ip = get_client_ip(request)
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
