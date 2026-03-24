from rest_framework.permissions import BasePermission


def tiene_rol(user, *roles):
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name__in=roles).exists()


class DenegarPorDefecto(BasePermission):
    message = "Acceso denegado"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.exists()

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.exists()


class EsAdmin(BasePermission):
    message = "Se requiere rol de Administrador"

    def has_permission(self, request, view):
        return tiene_rol(request.user, "Admin")

    def has_object_permission(self, request, view, obj):
        return tiene_rol(request.user, "Admin")


class EsGerenteOAdmin(BasePermission):
    message = "Se requiere rol de Gerente o Administrador"

    def has_permission(self, request, view):
        return tiene_rol(request.user, "Gerente", "Admin")

    def has_object_permission(self, request, view, obj):
        return tiene_rol(request.user, "Gerente", "Admin")


class EsEmpleadoOSuperior(BasePermission):
    message = "Se requiere al menos rol de Empleado"

    def has_permission(self, request, view):
        return tiene_rol(request.user, "Empleado", "Gerente", "Admin")

    def has_object_permission(self, request, view, obj):
        return tiene_rol(request.user, "Empleado", "Gerente", "Admin")


class PermisoInventario(BasePermission):
    """
    GET    → Empleado, Gerente, Admin
    POST   → Gerente, Admin
    PUT    → Gerente, Admin
    PATCH  → Gerente, Admin
    DELETE → Solo Admin activo
    """
    message = "No tienes permisos para esta acción"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.user.groups.exists():
            return False

        if request.method == "GET":
            return tiene_rol(request.user, "Empleado", "Gerente", "Admin")

        if request.method in ["POST", "PUT", "PATCH"]:
            return tiene_rol(request.user, "Gerente", "Admin")

        if request.method == "DELETE":
 
            return tiene_rol(request.user, "Admin") and request.user.is_active

        return False

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.user.groups.exists():
            return False

        if request.method == "GET":
            return tiene_rol(request.user, "Empleado", "Gerente", "Admin")

        if request.method in ["PUT", "PATCH"]:
            return tiene_rol(request.user, "Gerente", "Admin")

        if request.method == "DELETE":

            return tiene_rol(request.user, "Admin") and request.user.is_active

        return False

class PermisoBulk(BasePermission):
    
    message = "Las operaciones masivas requieren rol de Administrador"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.user.groups.exists():
            return False

        return tiene_rol(request.user, "Admin") and request.user.is_active

    def has_object_permission(self, request, view, obj):
        return tiene_rol(request.user, "Admin") and request.user.is_active