import pyotp
import qrcode
import io
import base64
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication 
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import authenticate
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from .models import InventoryItem, UserTOTP
from .serializers import InventoryItemSerializer


def registrar_log(user, accion, objeto):
    """Registra una acción en el log de Django Admin"""
    LogEntry.objects.create(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(InventoryItem).pk,
        object_id=str(objeto.pk),
        object_repr=str(objeto)[:200],
        action_flag=accion,
        change_message='',
    )


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    authentication_classes = [JWTAuthentication] 
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


# Autenticación TOTP----------------------------


@api_view(["POST"])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if not user:
        return Response({"error": "Credenciales incorrectas"}, status=400)

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


@api_view(["POST"])
def logout_view(request):

    django_logout(request)

    return Response({"message": "Sesión cerrada correctamente"}, status=200)


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
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    )
    # .....................................................
