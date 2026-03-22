import requests
import os

def verificar_turnstile(token: str, ip: str = None) -> bool:
    """Verifica el token de Cloudflare Turnstile"""
    secret_key = os.getenv("TURNSTILE_SECRET_KEY")

    data = {
        "secret": secret_key,
        "response": token,
    }

    if ip:
        data["remoteip"] = ip

    try:
        response = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data=data,
            timeout=5,
        )
        result = response.json()
        return result.get("success", False)

    except Exception:
        return False