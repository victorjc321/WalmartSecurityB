from rest_framework import serializers
from .models import InventoryItem, Supplier, ReviewInventory
from django.core.validators import RegexValidator
from django.contrib.auth import authenticate
import unicodedata
import re

DANGEROUS_PATTERNS = re.compile(
    r"(--|;|/\*|\*/|xp_|"
    r"UNION\s+SELECT|DROP\s+TABLE|"
    r"INSERT\s+INTO|DELETE\s+FROM|"
    r"ALTER\s+TABLE|CREATE\s+TABLE|TRUNCATE|"
    r"<script|</script|javascript:|vbscript:|"
    r"on\w+\s*=|data:\s*text/html|"
    r"eval\s*\(|exec\s*\(|system\s*\(|"
    r"__import__|subprocess|os\.system|"
    r"base64\s*,|\\x[0-9a-fA-F]{2})",
    re.IGNORECASE
)


def contains_dangerous_patterns(value: str) -> bool:
    return bool(DANGEROUS_PATTERNS.search(value))


def sanitize_text(value):
    value = unicodedata.normalize("NFKC", value).strip()

    if contains_dangerous_patterns(value):
        raise serializers.ValidationError("Entrada no permitida.")

    return value

USERNAME_VALIDATOR = RegexValidator(
    regex=r"^[a-zA-Z0-9._@+-]+$",
    message="Formato inválido."
)

# Serializador del inventario
class InventoryItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        min_length=3,
        max_length=255,
        trim_whitespace=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ\s\-\(\)\.]+$",
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
        value = sanitize_text(value)
        query = InventoryItem.objects.filter(product_name__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("Este producto ya existe.")
        return value

    def validate(self, attrs):
        extra = set(self.initial_data.keys()) - set(self.fields.keys())
        if extra:
            raise serializers.ValidationError("Campos no permitidos.")

        read_only_attempted = set(self.initial_data.keys()) & set(self.Meta.read_only_fields)
        if read_only_attempted:
            raise serializers.ValidationError(
                f"Campos no modificables: {read_only_attempted}"
            )

        price = attrs.get("unit_price")
        stock = attrs.get("quantity_in_stock")
        if price is not None and stock is not None:
            if price == 0 and stock > 0:
                raise serializers.ValidationError(
                    "Un producto con stock no puede tener precio cero."
                )

        return attrs

# Serializacion de login
class LoginSerializer(serializers.Serializer):

    username = serializers.CharField(
        min_length=3,
        max_length=150,
        trim_whitespace=True,
        validators=[USERNAME_VALIDATOR]
    )

    password = serializers.CharField(
        min_length=8,
        max_length=128,
        write_only=True,
        trim_whitespace=False
    )

    def validate_username(self, value):
        return sanitize_text(value)

    def validate_password(self, value):
        if contains_dangerous_patterns(value):
            raise serializers.ValidationError("Entrada no permitida.")
        return value

    def validate(self, attrs):
        extra = set(self.initial_data.keys()) - set(self.fields.keys())
        if extra:
            raise serializers.ValidationError("Campos no permitidos.")

        user = authenticate(
            username=attrs.get("username"),
            password=attrs.get("password")
        )

        if not user or not user.is_active:
            raise serializers.ValidationError("Credenciales inválidas.")

        attrs["user"] = user
        return attrs

# Serializador de verificación TOTP
class TOTPVerifySerializer(serializers.Serializer):

    username = serializers.CharField(
        min_length=3,
        max_length=150,
        trim_whitespace=True,
        validators=[USERNAME_VALIDATOR]
    )

    codigo = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={"invalid": "Código inválido."}
    )

    def validate_username(self, value):
        return sanitize_text(value)

    def validate(self, attrs):
        extra = set(self.initial_data.keys()) - set(self.fields.keys())
        if extra:
            raise serializers.ValidationError("Campos no permitidos.")

        return attrs


class SupplierSerializer(serializers.ModelSerializer):

    name = serializers.CharField(
        min_length=2,
        max_length=255,
        trim_whitespace=True,
    )

    class Meta:
        model = Supplier
        fields = ('supplier_id', 'name', 'created_at', 'updated_at')
        read_only_fields = ('supplier_id', 'created_at', 'updated_at')

    def validate_name(self, value):
        value = sanitize_text(value)
        query = Supplier.objects.filter(name__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("Este proveedor ya existe.")
        return value
    
# Serializacion de resenas
class ReviewInventorySerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source="item.product_name", read_only=True)

    rating = serializers.IntegerField(
        min_value=1,
        max_value=5
    )

    comment = serializers.CharField(
        min_length=3,
        max_length=500,
        trim_whitespace=True
    )

    class Meta:
        model = ReviewInventory
        fields = (
            'review_id',
            'item',
            'product_name',
            'rating',
            'comment',
            'reviewed_at'
        )
        read_only_fields = ('review_id', 'reviewed_at', 'product_name')

    def validate_comment(self, value):
        return sanitize_text(value)

    def validate(self, attrs):
        extra = set(self.initial_data.keys()) - set(self.fields.keys())
        if extra:
            raise serializers.ValidationError("Campos no permitidos.")

        read_only_attempted = set(self.initial_data.keys()) & set(self.Meta.read_only_fields)
        if read_only_attempted:
            raise serializers.ValidationError(
                f"Campos no modificables: {read_only_attempted}"
            )

        return attrs