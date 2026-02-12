from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

# Create your models here.
class InventoryItem(models.Model):
    item_id = models.UUIDField(
    primary_key=True,
    default=uuid.uuid4,
    editable=False
    )

    product_name = models.CharField(
        max_length=255,
        db_index=True
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    quantity_in_stock = models.PositiveIntegerField(
        validators=[MinValueValidator(0)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_asset"
        ordering = ["-created_at"]