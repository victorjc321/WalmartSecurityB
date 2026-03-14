from rest_framework import viewsets, permissions
from .models import InventoryItem
from .serializers import InventoryItemSerializer

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all() 
    permission_classes = [permissions.AllowAny]
    serializer_class = InventoryItemSerializer