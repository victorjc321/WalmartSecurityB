from .models import BlockedIP, UserSession
from django.http import JsonResponse
from django.contrib.auth import logout


class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")

        if BlockedIP.objects.filter(ip=ip, is_active=True).exists():
            return JsonResponse({"error": "IP bloqueada"}, status=403)

        if hasattr(request, "user") and request.user.is_authenticated:
            try:
                session_db = UserSession.objects.get(user=request.user)

                current_ip = request.META.get("REMOTE_ADDR")
                current_agent = request.META.get("HTTP_USER_AGENT")

                if (
                    session_db.session_key != request.session.session_key
                    or session_db.ip != current_ip
                    or session_db.user_agent != current_agent
                ):
                    user = request.user

                    logout(request)

                    UserSession.objects.filter(user=user).delete()

                    return JsonResponse(
                        {
                            "error": "Posible robo de sesión detectado o sesión en otro dispositivo"
                        },
                        status=401,
                    )

            except UserSession.DoesNotExist:
                pass

        response = self.get_response(request)

        if hasattr(response, "__setitem__") and request.path.startswith("/api/"):
            response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response
