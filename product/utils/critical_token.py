import jwt
import uuid
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from product.models import UsedCriticalToken


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


def validar_critical_token(token, user, session_key):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        jti = payload.get("jti")

        if not jti:
            return False

        if payload["user_id"] != user.id:
            return False

        if payload["session_key"] != session_key:
            return False

        obj, created = UsedCriticalToken.objects.get_or_create(jti=jti)
        if not created:
            return False

        return True

    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False
