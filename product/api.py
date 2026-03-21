import pyotp
import qrcode
import io
from datetime import timedelta
import base64
from .discord_logger import enviar_discord
from django.utils.timezone import now
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import logout as django_logout
from .models import InventoryItem, UserTOTP, FailedLoginAttempt
from .serializers import InventoryItemSerializer
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.views import APIView
from .models import FailedLoginAttempt
from django.utils.timezone import now
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from django.http import JsonResponse
from .discord_logger import enviar_discord
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)


def registrar_log(user, accion, objeto):
    """Registra una acción en el log de Django Admin"""
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(InventoryItem).pk,
        object_id=objeto.pk,
        object_repr=str(objeto),
        action_flag=accion,
    )


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        obj = serializer.save()
        if self.request.user.is_authenticated:
            registrar_log(self.request.user, ADDITION, obj)

    def perform_update(self, serializer):
        obj = serializer.save()
        if self.request.user.is_authenticated:
            registrar_log(self.request.user, CHANGE, obj)

    def perform_destroy(self, instance):
        if self.request.user.is_authenticated:
            registrar_log(self.request.user, DELETION, instance)
        instance.delete()


@api_view(["POST"])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    ip = request.META.get("REMOTE_ADDR")

    attempt, _ = FailedLoginAttempt.objects.get_or_create(ip=ip)

    if attempt.is_currently_blocked():
        return Response(
            {"error": "IP bloqueada", "blocked_until": attempt.blocked_until},
            status=403,
        )

    user = authenticate(username=username, password=password)

    if not user:
        attempt.attempts += 1

        # 🔥 BLOQUEOS PROGRESIVOS
        if attempt.attempts == 5:
            attempt.blocked_until = now() + timedelta(minutes=10)
            attempt.is_blocked = True

        elif attempt.attempts == 10:
            attempt.blocked_until = now() + timedelta(minutes=30)
            attempt.is_blocked = True

        elif attempt.attempts == 15:
            attempt.blocked_until = now() + timedelta(hours=1)
            attempt.is_blocked = True

        attempt.save()

        remaining = max(0, 5 - attempt.attempts)

        return Response(
            {"error": "Credenciales incorrectas", "remaining_attempts": remaining},
            status=400,
        )

    # ✅ LOGIN CORRECTO → RESET
    attempt.attempts = 0
    attempt.is_blocked = False
    attempt.blocked_until = None
    attempt.save()

    totp_obj, created = UserTOTP.objects.get_or_create(
        user=user, defaults={"totp_secret": pyotp.random_base32()}
    )

    if not totp_obj.is_configured:

        totp = pyotp.TOTP(totp_obj.totp_secret)
        uri = totp.provisioning_uri(name=user.username, issuer_name="Walmart México")

        img = qrcode.make(uri)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response(
            {
                "step": "setup",
                "qr": qr_base64,
                "mensaje": "Escanea el QR con Google Authenticator",
            }
        )

    return Response(
        {"step": "verify", "mensaje": "Ingresa el código de tu app autenticadora"}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_session(request):
    return Response({"authenticated": True})


@api_view(["POST"])
def logout_view(request):
    refresh_token = request.COOKIES.get("refresh_token")

    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except:
            pass

    response = Response({"message": "Logout exitoso"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_all_view(request):
    user = request.user

    tokens = OutstandingToken.objects.filter(user=user)

    for token in tokens:
        BlacklistedToken.objects.get_or_create(token=token)

    response = Response({"message": "Sesiones cerradas en todos los dispositivos"})

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response


@api_view(["POST"])
def verificar_totp_view(request):
    username = request.data.get("username")
    codigo = request.data.get("codigo")

    try:
        user = User.objects.get(username=username)
        totp_obj = UserTOTP.objects.get(user=user)
    except:
        return Response({"error": "Usuario no encontrado"}, status=400)

    totp = pyotp.TOTP(totp_obj.totp_secret)
    if not totp.verify(codigo):
        return Response({"error": "Código incorrecto o expirado"}, status=400)

    if not totp_obj.is_configured:
        totp_obj.is_configured = True
        totp_obj.save()

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    response = Response({"message": "Login exitoso"})

    # 🍪 Access token
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # ⚠️ en local pon False
        samesite="Lax",  # ⚠️Poner en None antes de subir
        max_age=60 * 10,
    )

    # 🍪 Refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # ⚠️ en local pon False
        samesite="Lax",  # ⚠️Poner en None antes de subir
        max_age=60 * 60 * 24,
    )

    # Notificacion del login a discord
    mensaje = f"LOGIN\nUsuario: {user.username}"
    enviar_discord(mensaje, 5763719)

    return response


@ensure_csrf_cookie
@api_view(["GET"])
def csrf_view(request):
    return Response({"message": "CSRF cookie set"})


class RefreshView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response({"error": "No refresh token"}, status=401)

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)

            access_token = serializer.validated_data["access"]
            new_refresh = serializer.validated_data.get("refresh")

            response = Response({"message": "Token renovado"})

            # 🍪 Access token
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=False,  # ⚠️ en local pon False
                samesite="Lax",  # ⚠️Poner en None antes de subir
                max_age=60 * 10,
            )

            # 🍪 Refresh ROTADO
            if new_refresh:
                response.set_cookie(
                    key="refresh_token",
                    value=new_refresh,
                    httponly=True,
                    secure=False,  # ⚠️ en local pon False
                    samesite="Lax",  # ⚠️Poner en None antes de subir
                    max_age=60 * 60 * 24,
                )

            return response

        except TokenError:
            print("⚠️ POSIBLE ROBO DE TOKEN DETECTADO")

            response = Response({"error": "Sesión comprometida"}, status=401)

            # 🔥 eliminar cookies
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")

            return response
