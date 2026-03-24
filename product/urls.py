from django.urls import path
from .api import InventoryItemViewSet
from .api import InventoryItemViewSet, BulkDeleteView

inventory_list = InventoryItemViewSet.as_view({
    'get': 'list',       
    'post': 'create',    
})

inventory_detail = InventoryItemViewSet.as_view({
    'get': 'retrieve',   
    'patch': 'partial_update',  
    'delete': 'destroy', 
   
    
})

urlpatterns = [
    path('inventory/', inventory_list, name='inventory-list'),
    path('inventory/bulk/', BulkDeleteView.as_view(), name='inventory-bulk-delete'),
    path('inventory/<uuid:pk>/', inventory_detail, name='inventory-detail'),
]