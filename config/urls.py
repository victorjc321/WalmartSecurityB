from django.contrib import admin
from django.urls import path, include
from product.api import mi_rol_view
from product.api import session_expired_view
from django.http import JsonResponse
from django.conf import settings
from product.api import (
    login_view,
    mi_rol_view,
    verificar_totp_view,
    logout_view,
    RefreshView,
    csrf_view,
    logout_all_view,
    check_session,
    verify_critical_view,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("product.urls")),
    path("api/login/", login_view),
    path("api/verificar-totp/", verificar_totp_view),
    path("api/logout/", logout_view),
    path("csrf/", csrf_view),
    path("refresh/", RefreshView.as_view()),
    path("logout-all/", logout_all_view),
    path("api/check-session/", check_session),
    path("api/session-expired/", session_expired_view),
    path("api/mi-rol/", mi_rol_view),
    path("api/verify-critical/", verify_critical_view),
]

if settings.ENVIRONMENT != "production":
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
    ]
