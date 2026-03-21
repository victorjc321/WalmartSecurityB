from rest_framework.throttling import SimpleRateThrottle
from django.conf import settings


def get_ip(request):
    if getattr(settings, 'TRUSTED_PROXY', False):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class IPRateThrottle(SimpleRateThrottle):
    scope = 'ip'

    def get_cache_key(self, request, view):
        ip = get_ip(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ip
        }


class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login'

    def get_cache_key(self, request, view):
        ip = get_ip(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ip
        }


class AuthSessionThrottle(SimpleRateThrottle):
    scope = 'auth_session'

    def get_cache_key(self, request, view):
        ip = get_ip(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ip
        }