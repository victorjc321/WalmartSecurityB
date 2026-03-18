from rest_framework import serializers
from .models import InventoryItem
from django.core.validators import RegexValidator
import unicodedata

def normalize_text(value):
    # limpia espacios y normaliza unicode
    return unicodedata.normalize("NFKC", value).strip()

class InventoryItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        min_length=3,
        max_length=255,
        trim_whitespace=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-\(\)\.]+$",
                message="El nombre contiene caracteres no permitidos."
            )
        ]
    )

    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        max_value=100000
    )

    quantity_in_stock = serializers.IntegerField(
        min_value=0,
        max_value=200
    )

    class Meta:
        model = InventoryItem
        fields = (
            'item_id',
            'product_name',
            'unit_price',
            'quantity_in_stock',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('item_id', 'created_at', 'updated_at')

    def validate_product_name(self, value):
        # evita duplicados y normaliza
        value = normalize_text(value)

        query = InventoryItem.objects.filter(product_name__iexact=value)

        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("Este producto ya existe.")

        return value

    def validate(self, attrs):
        # valida relación precio-stock
        price = attrs.get("unit_price")
        stock = attrs.get("quantity_in_stock")

        if price is not None and stock is not None:
            if price == 0 and stock > 0:
                raise serializers.ValidationError(
                    "Un producto con stock no puede tener precio cero."
                )

        return attrs

class LoginSerializer(serializers.Serializer):

    username = serializers.CharField(
        min_length=3,
        max_length=150,
        trim_whitespace=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9._@+-]+$",
                message="Formato inválido."
            )
        ]
    )

    password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        trim_whitespace=False
    )

    def validate_username(self, value):
        # limpia y normaliza
        return normalize_text(value)

class TOTPVerifySerializer(serializers.Serializer):

    username = serializers.CharField(
        min_length=3,
        max_length=150,
        trim_whitespace=True
    )

    codigo = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={"invalid": "Código inválido."}
    )

    def validate_username(self, value):
        # limpia y normaliza
        return normalize_text(value)