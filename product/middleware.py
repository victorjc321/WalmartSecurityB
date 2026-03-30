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

                if session_db.session_key != request.session.session_key:
                    logout(request)
                    return JsonResponse(
                        {"error": "Sesión inválida o iniciada en otro dispositivo"},
                        status=401,
                    )

            except UserSession.DoesNotExist:
                pass

        try:
            response = self.get_response(request)
        except Exception as e:
            print("Middleware error:", e)
            raise e

        if hasattr(response, "__setitem__"):
            if request.path.startswith("/api/"):
                response["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response["Pragma"] = "no-cache"
                response["Expires"] = "0"

        return response
