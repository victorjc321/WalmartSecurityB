from rest_framework.permissions import BasePermission


def tiene_rol(user, *roles):
    """Verifica si el usuario pertenece a alguno de los roles dados"""
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name__in=roles).exists()



class DenegarPorDefecto(BasePermission):
    """
    Si el usuario no tiene ningún rol asignado
    se le deniega el acceso a todo
    """
    message = "Acceso denegado"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Debe pertenecer a al menos un grupo
        return request.user.groups.exists()




class EsAdmin(BasePermission):
    """Acceso total — solo Admin"""
    message = "Se requiere rol de Administrador"

    def has_permission(self, request, view):
        return tiene_rol(request.user, "Admin")


class EsGerenteOAdmin(BasePermission):
    """Puede ver y editar — Gerente o Admin"""
    message = "Se requiere rol de Gerente o Administrador"

    def has_permission(self, request, view):
        return tiene_rol(request.user, "Gerente", "Admin")


class EsEmpleadoOSuperior(BasePermission):
    """Solo lectura — Empleado, Gerente o Admin"""
    message = "Se requiere al menos rol de Empleado"

    def has_permission(self, request, view):
        return tiene_rol(request.user, "Empleado", "Gerente", "Admin")



class PermisoInventario(BasePermission):
    """
    GET    → Empleado, Gerente, Admin
    POST   → Gerente, Admin
    PUT    → Gerente, Admin
    PATCH  → Gerente, Admin
    DELETE → Solo Admin
    """
    message = "No tienes permisos para esta acción"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Sin rol — deniega por defecto
        if not request.user.groups.exists():
            return False

        if request.method == "GET":
            return tiene_rol(request.user, "Empleado", "Gerente", "Admin")

        if request.method in ["POST", "PUT", "PATCH"]:
            return tiene_rol(request.user, "Gerente", "Admin")

        if request.method == "DELETE":
            return tiene_rol(request.user, "Admin")

        return False