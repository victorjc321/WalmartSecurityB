from .models import BlockedIP
from django.http import JsonResponse


class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")

        if BlockedIP.objects.filter(ip=ip, is_active=True).exists():
            return JsonResponse({"error": "IP bloqueada"}, status=403)

        try:
            response = self.get_response(request)
        except Exception as e:
            print("Middleware error:", e)
            raise e

        # 🔥 SOLO si response es válido
        if hasattr(response, "__setitem__"):
            if request.path.startswith("/api/"):
                response["Cache-Control"] = (
                    "no-store, no-cache, must-revalidate, max-age=0"
                )
                response["Pragma"] = "no-cache"
                response["Expires"] = "0"

        return response
