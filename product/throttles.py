from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle
from .utils.security import get_client_ip


class IPRateThrottle(SimpleRateThrottle):
    scope = "ip"

    def get_cache_key(self, request, view):
        ip = get_client_ip(request)
        return self.cache_format % {"scope": self.scope, "ident": ip}


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        ip = get_client_ip(request)
        return self.cache_format % {"scope": self.scope, "ident": ip}


class AuthSessionThrottle(SimpleRateThrottle):
    scope = "auth_session"

    def get_cache_key(self, request, view):
        ip = get_client_ip(request)
        return self.cache_format % {"scope": self.scope, "ident": ip}


class SupplierCreateThrottle(UserRateThrottle):
    scope = "supplier_create"

    def get_cache_key(self, request, view):
        ip = get_client_ip(request)
        return self.cache_format % {"scope": self.scope, "ident": ip}
