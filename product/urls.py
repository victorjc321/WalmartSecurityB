from django.urls import path
from .api import InventoryItemViewSet, BulkDeleteView, SupplierViewSet, ReviewInventoryViewSet

inventory_list = InventoryItemViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

inventory_detail = InventoryItemViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy',
})

supplier_list = SupplierViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

supplier_detail = SupplierViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy',
})

review_list = ReviewInventoryViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

review_detail = ReviewInventoryViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    path('inventory/', inventory_list, name='inventory-list'),
    path('inventory/bulk/', BulkDeleteView.as_view(), name='inventory-bulk-delete'),
    path('inventory/<uuid:pk>/', inventory_detail, name='inventory-detail'),
    path('suppliers/', supplier_list, name='supplier-list'),
    path('suppliers/<uuid:pk>/', supplier_detail, name='supplier-detail'),
    path('reviews/', review_list, name='review-list'),
    path('reviews/<uuid:pk>/', review_detail, name='review-detail'),
]