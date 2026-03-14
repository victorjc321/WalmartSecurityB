from rest_framework import serializers
from .models import InventoryItem

class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ('item_id', 'product_name', 'unit_price', 'quantity_in_stock', 'created_at', 'updated_at')
        read_only_fields = ('item_id', 'created_at', 'updated_at')