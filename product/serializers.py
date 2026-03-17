from rest_framework import serializers
from .models import InventoryItem
import re

# Serializador para el modelo InventoryItem (CRUD)
class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ('item_id', 'product_name', 'unit_price', 'quantity_in_stock', 'created_at', 'updated_at')
        read_only_fields = ('item_id', 'created_at', 'updated_at')

        # Reglas básicas del campo nombre
        extra_kwargs = {
            "product_name": {
                "required": True,
                "allow_blank": False,
                "trim_whitespace": True,
            }
        }

    # Bloquea campos que no existan en el serializer
    def to_internal_value(self, data):
        allowed = set(self.fields.keys())

        for field in data.keys():
            if field not in allowed:
                raise serializers.ValidationError("Campo no permitido.")

        return super().to_internal_value(data)

    # Valida nombre
    def validate_product_name(self, value):

        # Verifica que sea texto
        if not isinstance(value, str):
            raise serializers.ValidationError("Formato inválido.")

        # Quita espacios al inicio y final
        value = value.strip()

        # Evita productos duplicados
        query = InventoryItem.objects.filter(product_name__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("Este producto ya existe.")

        # Normaliza el formato del nombre
        value = value.strip().title()

        # Longitud minima
        if len(value) < 3:
            raise serializers.ValidationError(
                "El nombre debe tener mínimo 3 caracteres."
            )

        # Longitud maxima
        if len(value) > 255:
            raise serializers.ValidationError(
                "El nombre excede el tamaño permitido."
            )

        # Permite solo caracteres seguros
        patron = r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\-\(\)\.]+$"
        if not re.match(patron, value):
            raise serializers.ValidationError(
                "El nombre contiene caracteres no permitidos."
            )

        # Detecta payloads sospechosos
        palabras_prohibidas = [
            "<script",
            "</script",
            "select ",
            "drop ",
            "insert ",
            "delete ",
            "--",
        ]

        lower = value.lower()

        for palabra in palabras_prohibidas:
            if palabra in lower:
                raise serializers.ValidationError(
                    "Contenido sospechoso detectado."
                )

        return value

    # Valida precio
    def validate_unit_price(self, value):

        # Debe existir
        if value is None:
            raise serializers.ValidationError("El precio es obligatorio.")

        # No permite valores negativos
        if value <= 0:
            raise serializers.ValidationError(
                "El precio debe ser mayor que cero."
            )

        # Límite maximo permitido
        if value > 100000:
            raise serializers.ValidationError(
                "Precio fuera de rango permitido."
            )

        return value

    # Valida la cantidad en stock
    def validate_quantity_in_stock(self, value):

        # Debe existir
        if value is None:
            raise serializers.ValidationError("La cantidad es obligatoria.")

        # No permite negativos
        if value < 0:
            raise serializers.ValidationError(
                "La cantidad no puede ser negativa."
            )

        # Limite maximo permitido
        if value > 200:
            raise serializers.ValidationError(
                "Cantidad fuera de rango permitido."
            )

        return value

    # Valida relacion entre campos
    def validate(self, attrs):

        price = attrs.get("unit_price")
        stock = attrs.get("quantity_in_stock")

        # Evita productos con stock pero sin precio
        if price and stock is not None:

            if price == 0 and stock > 0:
                raise serializers.ValidationError(
                    "Un producto con stock no puede tener precio cero."
                )

        return attrs

# Serializer para el login inicial (username y password)
class LoginSerializer(serializers.Serializer):

    username = serializers.CharField(
        max_length=150,
        trim_whitespace=True
    )

    password = serializers.CharField(
        max_length=128,
        write_only=True
    )

    # valida y sanitiza username
    def validate_username(self, value):

        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError("Formato inválido.")

        patron = r"^[a-zA-Z0-9._@+-]+$"
        if not re.match(patron, value):
            raise serializers.ValidationError("Formato inválido.")

        return value

# Serializer para verificar el código TOTP
class TOTPVerifySerializer(serializers.Serializer):

    username = serializers.CharField(
        max_length=150,
        trim_whitespace=True
    )

    codigo = serializers.CharField(
        max_length=6,
        min_length=6
    )

    def validate_codigo(self, value):

        if not value.isdigit():
            raise serializers.ValidationError("Código inválido.")

        return value