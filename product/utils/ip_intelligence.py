import requests
from django.conf import settings

IPQS_URL = "https://ipqualityscore.com/api/json/ip"


def check_ip_reputation(ip):
    try:
        url = f"{IPQS_URL}/{settings.IPQS_API_KEY}/{ip}"
        response = requests.get(url, timeout=3)
        data = response.json()

        return {
            "vpn": data.get("vpn", False),
            "proxy": data.get("proxy", False),
            "tor": data.get("tor", False),
            "fraud_score": data.get("fraud_score", 0),
            "country": data.get("country_code"),
        }

    except Exception:
        return {
            "vpn": False,
            "proxy": False,
            "tor": False,
            "fraud_score": 0,
            "country": None,
        }
