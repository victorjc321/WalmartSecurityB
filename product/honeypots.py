from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils.security import get_client_ip
from .utils.security_logger import log_security_event
from .models import BlockedIP


def bloquear_ip(ip, reason="honeypot"):
    BlockedIP.objects.update_or_create(
        ip=ip, defaults={"is_active": True, "reason": reason}
    )


@api_view(["GET", "POST"])
def fake_admin(request):
    ip = get_client_ip(request)

    log_security_event(
        request, "RISK_DETECTED", extra={"type": "honeypot_admin_access"}
    )

    bloquear_ip(ip, "Intento acceso admin falso")

    return Response({"error": "Acceso denegado"}, status=403)


@api_view(["GET"])
def fake_env(request):
    ip = get_client_ip(request)

    log_security_event(request, "RISK_DETECTED", extra={"type": "honeypot_env_access"})

    bloquear_ip(ip, "Intento acceso .env")

    return Response({"error": "Archivo no encontrado"}, status=404)
