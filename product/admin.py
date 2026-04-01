from django.contrib import admin
from django.contrib.admin.models import LogEntry
from .models import InventoryItem, Supplier


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("product_name", "unit_price", "quantity_in_stock", "created_at")
    search_fields = ("product_name",)
    list_filter = ("created_at",)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ("action_time", "user", "content_type", "object_repr", "action_flag")
    list_filter = ("action_flag", "content_type")
    search_fields = ("user__username", "object_repr")
    readonly_fields = (
        "action_time", "user", "content_type",
        "object_id", "object_repr", "action_flag", "change_message"
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
    list_filter = ("created_at",)