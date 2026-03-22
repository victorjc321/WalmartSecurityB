from rest_framework.response import Response
from django.utils.timezone import now
from .critical_token import validar_critical_token


def requiere_token_critico(request):
    token = request.headers.get("X-Critical-Token")

    if not token:
        return False

    return validar_critical_token(token, request.user, request.session.session_key)
