from django.db import models
from django.core.validators import MinValueValidator
import pyotp
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid


class UserTOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    totp_secret = models.CharField(max_length=32)
    is_configured = models.BooleanField(default=False)

    def __str__(self):
        return f"TOTP - {self.user.username}"


class InventoryItem(models.Model):
    item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_name = models.CharField(max_length=255, db_index=True)
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))]
    )
    quantity_in_stock = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name

    class Meta:
        db_table = "inventory_asset"
        ordering = ["-created_at"]


class BlockedIP(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    reason = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.ip


class FailedLoginAttempt(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    attempts = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(null=True, blank=True)

    def is_currently_blocked(self):
        if self.is_blocked and self.blocked_until:
            if timezone.now() >= self.blocked_until:
                self.is_blocked = False
                self.attempts = 0
                self.blocked_until = None
                self.save()
                return False
            return True
        return False

    def apply_block(self):
        if self.attempts >= 7:
            self.blocked_until = timezone.now() + timedelta(hours=1)
        elif self.attempts >= 5:
            self.blocked_until = timezone.now() + timedelta(minutes=30)
        elif self.attempts >= 3:
            self.blocked_until = timezone.now() + timedelta(minutes=5)
        self.is_blocked = True

    def __str__(self):
        return f"{self.ip} - {self.attempts}"


class FailedTOTPAttempt(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    attempts = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    is_blocked = models.BooleanField(default=False)
    blocked_until = models.DateTimeField(null=True, blank=True)

    def is_currently_blocked(self):
        if self.is_blocked and self.blocked_until:
            if timezone.now() >= self.blocked_until:
                self.is_blocked = False
                self.attempts = 0
                self.blocked_until = None
                self.save()
                return False
            return True
        return False

    def apply_block(self):
        if self.attempts >= 7:
            self.blocked_until = timezone.now() + timedelta(hours=1)
        elif self.attempts >= 5:
            self.blocked_until = timezone.now() + timedelta(minutes=30)
        elif self.attempts >= 3:
            self.blocked_until = timezone.now() + timedelta(minutes=5)
        self.is_blocked = True

    def __str__(self):
        return f"{self.user.username} - {self.attempts} intentos"