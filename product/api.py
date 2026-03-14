from rest_framework import viewsets, permissions
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from .models import InventoryItem
from .serializers import InventoryItemSerializer


def registrar_log(user, accion, objeto):
    """Registra una acción en el log de Django Admin"""
    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(InventoryItem).pk,
        object_id=objeto.pk,
        object_repr=str(objeto),
        action_flag=accion,
    )


class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [permissions.AllowAny]  # <- se mantiene igual que tenías

    def perform_create(self, serializer):
        obj = serializer.save()
        if self.request.user.is_authenticated:
            registrar_log(self.request.user, ADDITION, obj)

    def perform_update(self, serializer):
        obj = serializer.save()
        if self.request.user.is_authenticated:
            registrar_log(self.request.user, CHANGE, obj)

    def perform_destroy(self, instance):
        if self.request.user.is_authenticated:
            registrar_log(self.request.user, DELETION, instance)
        instance.delete()