from django.contrib import admin
from django.urls import path, include
from product.api import login_view, verificar_totp_view
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('product.urls')),
    path('api/login/', login_view),
    path('api/verificar-totp/', verificar_totp_view),
]
