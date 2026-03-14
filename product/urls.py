from rest_framework import routers
from .api import InventoryItemViewSet

router = routers.DefaultRouter()

router.register(r'inventory', InventoryItemViewSet, basename='inventory')
urlpatterns = router.urls