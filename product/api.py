import pyotp
import qrcode
import io
from datetime import timedelta
from django.utils.dateparse import parse_datetime
import base64
from datetime import timedelta
from .permissions import PermisoInventario, PermisoBulk
from .discord_logger import enviar_discord
from django.utils.timezone import now
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from .throttles import IPRateThrottle, LoginRateThrottle, AuthSessionThrottle
from rest_framework.throttling import UserRateThrottle
from .models import InventoryItem, UserTOTP, FailedLoginAttempt, FailedTOTPAttempt
from .serializers import InventoryItemSerializer
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)


# ─────────────────────────────────────────
# Log del admin
# ─────────────────────────────────────────


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mi_rol_view(request):
    grupos = list(request.user.groups.values_list("name", flat=True))
    return Response(
        {
            "username": request.user.username,
            "roles": grupos,
            "is_admin": "Admin" in grupos,
            "is_gerente": "Gerente" in grupos,
            "is_empleado": "Empleado" in grupos,
        }
    )


def registrar_log(user, accion, objeto):
    LogEntry.objects.create(
        user_id=user.id,
        content_type=ContentType.objects.get_for_model(InventoryItem),
        object_id=str(objeto.pk),
        object_repr=str(objeto)[:200],
        action_flag=accion,
        change_message="",
    )


# ─────────────────────────────────────────
# CRUD de inventario
# ─────────────────────────────────────────


class InventoryItemViewSet(viewsets.ModelViewSet):
    serializer_class = InventoryItemSerializer
    throttle_classes = [IPRateThrottle, UserRateThrottle]
    permission_classes = [PermisoInventario]

    def get_queryset(self):
        user = self.request.user

        if not user or not user.is_authenticated:
            return InventoryItem.objects.none()

        if not user.groups.exists():
            return InventoryItem.objects.none()

        return InventoryItem.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        if request.user.is_authenticated:
            registrar_log(request.user, CHANGE, obj)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_authenticated:
            registrar_log(request.user, DELETION, instance)
        instance.delete()
        return Response(status=204)

    def perform_create(self, serializer):
        obj = serializer.save()
        if self.request.user.is_authenticated:
            registrar_log(self.request.user, ADDITION, obj)


# ─────────────────────────────────────────
# Login
# ─────────────────────────────────────────


@api_view(["POST"])
@throttle_classes([IPRateThrottle, LoginRateThrottle])
@sensitive_variables("password")
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    ip = request.META.get("REMOTE_ADDR")
    attempt, _ = FailedLoginAttempt.objects.get_or_create(ip=ip)

    # ── Verifica bloqueo ANTES de autenticar ──
    if attempt.is_currently_blocked():
        return Response(
            {"error": "Acceso temporalmente restringido"},
            status=403,
        )

    user = authenticate(username=username, password=password)

    if not user:
        attempt.attempts += 1

        if attempt.attempts >= 3:
            attempt.apply_block()
            attempt.save()
            return Response(
                {"error": "Acceso temporalmente restringido"},
                status=403,
            )

        attempt.save()
        return Response(
            {"error": "Credenciales incorrectas"},
            status=400,
        )

    attempt.attempts = 0
    attempt.is_blocked = False
    attempt.blocked_until = None
    attempt.save()

    request.session["pre_2fa_user"] = user.id
    request.session.modified = True
    request.session["otp_attempts"] = 0
    request.session["otp_blocked_until"] = None

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
                "mensaje": "Escanea el QR con una Authenticator",
            }
        )

    return Response({"step": "verify", "mensaje": "Ingresa el código de autenticación"})


# ─────────────────────────────────────────
# Verificar sesión
# ─────────────────────────────────────────


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([AuthSessionThrottle])
def check_session(request):
    return Response({"authenticated": True})


# ─────────────────────────────────────────
# Logout
# ─────────────────────────────────────────


@api_view(["POST"])
@throttle_classes([AuthSessionThrottle])
def logout_view(request):
    user = request.user if request.user.is_authenticated else None

    refresh_token = request.COOKIES.get("refresh_token")

    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except:
            pass

    # 🔔 NOTIFICACIÓN DISCORD
    if user:
        mensaje = f"LOGOUT\nUsuario: {user.username}"
    else:
        mensaje = "LOGOUT\nUsuario desconocido (token expirado)"

    enviar_discord(mensaje, 16711680)

    response = Response({"message": "Logout exitoso"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response


@api_view(["POST"])
def session_expired_view(request):
    ip = request.META.get("REMOTE_ADDR")

    mensaje = f"""⚠️ SESIÓN EXPIRADA

IP: {ip}
Evento: Token expirado o inválido
"""

    enviar_discord(mensaje, 16776960)

    return Response({"message": "Evento registrado"})


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


# ─────────────────────────────────────────
# Verificar TOTP
# ─────────────────────────────────────────


@api_view(["POST"])
@throttle_classes([IPRateThrottle, LoginRateThrottle])
@sensitive_variables("codigo")
def verificar_totp_view(request):
    user_id = request.session.get("pre_2fa_user")

    if not user_id:
        return Response({"error": "Sesión inválida"}, status=403)

    try:
        user = User.objects.get(id=user_id)
        totp_obj = UserTOTP.objects.get(user=user)
    except:
        return Response({"error": "Acceso temporalmente restringido"}, status=400)

    totp_attempt, created = FailedTOTPAttempt.objects.get_or_create(user=user)

    # ── Verifica bloqueo por usuario ANTES de validar ──
    if totp_attempt.is_currently_blocked():
        return Response(
            {"error": "Acceso temporalmente restringido"},
            status=403,
        )

    # 🔥 CONTROL DE INTENTOS OTP
    attempts = request.session.get("otp_attempts", 0)
    blocked_until = request.session.get("otp_blocked_until")

    if blocked_until:
        blocked_until = parse_datetime(blocked_until)

    if blocked_until and now() < blocked_until:
        return Response(
            {
                "error": "Demasiados intentos OTP",
                "blocked_until": blocked_until,
            },
            status=403,
        )

    codigo = request.data.get("codigo")

    totp = pyotp.TOTP(totp_obj.totp_secret)

    if not totp.verify(codigo):
        attempts += 1
        request.session["otp_attempts"] = attempts

        if attempts == 5:
            request.session["otp_blocked_until"] = (
                now() + timedelta(minutes=5)
            ).isoformat()

        elif attempts == 10:
            request.session["otp_blocked_until"] = (
                now() + timedelta(minutes=15)
            ).isoformat()

        request.session.modified = True

        return Response(
            {"error": "Código incorrecto", "intentos": attempts}, status=400
        )

    request.session.pop("pre_2fa_user", None)
    request.session.pop("otp_attempts", None)
    request.session.pop("otp_blocked_until", None)

    if not totp_obj.is_configured:
        totp_obj.is_configured = True
        totp_obj.save()

    # 🔐 GENERAR TOKENS
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    response = Response({"message": "Login exitoso"})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=60 * 10,
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=60 * 60 * 24,
    )

    mensaje = f"LOGIN 2FA\nUsuario: {user.username}"
    enviar_discord(mensaje, 5763719)

    return response


# ─────────────────────────────────────────
# CSRF y Refresh
# ─────────────────────────────────────────


@api_view(["GET"])
@ensure_csrf_cookie
def csrf_view(request):
    return Response({"message": "CSRF cookie set"})


class RefreshView(APIView):
    @sensitive_variables("refresh_token", "access_token", "new_refresh")
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

            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=60 * 10,
            )

            if new_refresh:
                response.set_cookie(
                    key="refresh_token",
                    value=new_refresh,
                    httponly=True,
                    secure=False,
                    samesite="Lax",
                    max_age=60 * 60 * 24,
                )

            return response

        except TokenError:
            print("POSIBLE ROBO DE TOKEN DETECTADO")

            response = Response({"error": "Sesión comprometida"}, status=401)
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response


# ─────────────────────────────────────────
# Bulk Delete — Solo Admin
# ─────────────────────────────────────────


class BulkDeleteView(APIView):

    permission_classes = [PermisoBulk]
    throttle_classes = [IPRateThrottle, UserRateThrottle]

    def delete(self, request):
        ids = request.data.get("ids", [])

        if not ids or not isinstance(ids, list):
            return Response({"error": "Se requiere una lista de IDs"}, status=400)

        if len(ids) > 20:
            return Response({"error": "Máximo 20 productos por operación"}, status=400)

        items = InventoryItem.objects.filter(item_id__in=ids)

        if not items.exists():
            return Response({"error": "Ningún producto encontrado"}, status=404)

        for item in items:
            registrar_log(request.user, DELETION, item)

        count = items.count()
        items.delete()

        mensaje = f"BULK DELETE\nAdmin: {request.user.username}\nEliminados: {count} productos"
        enviar_discord(mensaje, 15158332)

        return Response({"message": f"{count} productos eliminados"}, status=200)
