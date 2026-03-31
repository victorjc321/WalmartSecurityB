import jwt
import uuid
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from product.models import UsedCriticalToken
from product.discord_logger import enviar_discord


def generar_critical_token(user, session_key):
    jti = str(uuid.uuid4())

    payload = {
        "user_id": user.id,
        "session_key": session_key,
        "scope": "critical",
        "jti": jti,
        "exp": now() + timedelta(minutes=2),
        "iat": now(),
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return token


def validar_critical_token(token, user, session_key, request=None):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        jti = payload.get("jti")

        if not jti:
            enviar_discord("🚨 TOKEN SIN JTI", 16711680, request)
            return False

        if payload.get("user_id") != user.id:
            enviar_discord("🚨 USER ID NO COINCIDE", 16711680, request)
            return False

        if payload.get("session_key") != session_key:
            enviar_discord("🚨 SESSION KEY NO COINCIDE", 16711680, request)
            return False

        obj, created = UsedCriticalToken.objects.get_or_create(jti=jti)
        if not created:
            enviar_discord("🚨 REPLAY DETECTADO", 16711680, request)
            return False

        return True

    except jwt.ExpiredSignatureError:
        enviar_discord("⚠️ TOKEN EXPIRADO", 16776960, request)
        return False

    except jwt.InvalidTokenError:
        enviar_discord("🚨 TOKEN INVÁLIDO", 16711680, request)
        return False
