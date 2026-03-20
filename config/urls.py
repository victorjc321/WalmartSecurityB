from django.contrib import admin
from django.urls import path, include


from product.api import (
    login_view,
    verificar_totp_view,
    logout_view,
    RefreshView,
    csrf_view,
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
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("refresh/", RefreshView.as_view()),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
