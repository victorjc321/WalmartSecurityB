import pyotp
import qrcode
import io
import base64
from datetime import timedelta
from .permissions import PermisoInventario
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
from .throttles import IPRateThrottle, LoginRateThrottle
from .throttles import IPRateThrottle, LoginRateThrottle
from rest_framework.throttling import UserRateThrottle
from .models import InventoryItem, UserTOTP, FailedLoginAttempt, FailedTOTPAttempt
from .serializers import InventoryItemSerializer
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


# ─────────────────────────────────────────
# Log del admin
# ─────────────────────────────────────────

def registrar_log(user, accion, objeto):
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(InventoryItem).pk,
        object_id=objeto.pk,
        object_repr=str(objeto),
        action_flag=accion,
    )
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mi_rol_view(request):
    grupos = list(request.user.groups.values_list("name", flat=True))
    return Response({
        "username": request.user.username,
        "roles": grupos,
        "is_admin": "Admin" in grupos,
        "is_gerente": "Gerente" in grupos,
        "is_empleado": "Empleado" in grupos,
    })

# ─────────────────────────────────────────
# CRUD de inventario
# ─────────────────────────────────────────

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    throttle_classes = [IPRateThrottle, UserRateThrottle]
    permission_classes = [PermisoInventario]

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


# ─────────────────────────────────────────
# Login
# ─────────────────────────────────────────

@api_view(["POST"])
@throttle_classes([LoginRateThrottle])
@sensitive_variables('password')
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

    # ── Login correcto — resetea intentos ──
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

        return Response({
            "step": "setup",
            "qr": qr_base64,
            "mensaje": "Escanea el QR con una Authenticator",
        })

    return Response({
        "step": "verify",
        "mensaje": "Ingresa el código de autenticación"
    })


# ─────────────────────────────────────────
# Verificar sesión
# ─────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_session(request):
    return Response({"authenticated": True})


# ─────────────────────────────────────────
# Logout
# ─────────────────────────────────────────

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


# ─────────────────────────────────────────
# Verificar TOTP
# ─────────────────────────────────────────

@api_view(["POST"])
@throttle_classes([LoginRateThrottle])
@sensitive_variables('codigo')
def verificar_totp_view(request):
    username = request.data.get("username")
    codigo = request.data.get("codigo")

    try:
        user = User.objects.get(username=username)
        totp_obj = UserTOTP.objects.get(user=user)
    except:
        return Response(
            {"error": "Acceso temporalmente restringido"}, status=400
        )

    totp_attempt, created = FailedTOTPAttempt.objects.get_or_create(user=user)

    # ── Verifica bloqueo por usuario ANTES de validar ──
    if totp_attempt.is_currently_blocked():
        return Response(
            {"error": "Acceso temporalmente restringido"},
            status=403,
        )

    totp = pyotp.TOTP(totp_obj.totp_secret)
    if not totp.verify(codigo):
        totp_attempt.attempts += 1

        if totp_attempt.attempts >= 3:
            totp_attempt.apply_block()
            totp_attempt.save()
            return Response(
                {"error": "Acceso temporalmente restringido"},
                status=403,
            )

        totp_attempt.save()
        return Response(
            {"error": "Código incorrecto o expirado"},
            status=400,
        )

    # ── Recarga desde BD para verificar si quedó bloqueado ──
    totp_attempt.refresh_from_db()

    if totp_attempt.is_currently_blocked():
        return Response(
            {"error": "Acceso temporalmente restringido"},
            status=403,
        )

   
    totp_attempt.attempts = 0
    totp_attempt.is_blocked = False
    totp_attempt.blocked_until = None
    totp_attempt.save()

    if not totp_obj.is_configured:
        totp_obj.is_configured = True
        totp_obj.save()

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

    mensaje = f"LOGIN\nUsuario: {user.username}"
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
    @sensitive_variables('refresh_token', 'access_token', 'new_refresh')
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
            print("⚠️POSIBLE ROBO DE TOKEN DETECTADO")
            response = Response({"error": "Sesión comprometida"}, status=401)
            response.delete_cookie("access_token")
            response.delete_cookie("refresh_token")
            return response