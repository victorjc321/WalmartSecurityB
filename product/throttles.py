from rest_framework.throttling import SimpleRateThrottle

class IPRateThrottle(SimpleRateThrottle):
    
    scope = 'ip'

    def get_cache_key(self, request, view):
        # Obtiene la IP real aunque esté detrás de un proxy
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
        return self.cache_format % {
            'scope': self.scope,
            'ident': ip
        }


class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login'

    def get_cache_key(self, request, view):
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
        return self.cache_format % {
            'scope': self.scope,
            'ident': ip
        }