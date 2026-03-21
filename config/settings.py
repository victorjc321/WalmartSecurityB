from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("SECRET_KEY")

# detecta el entorno para separar local vs producción
# pendiente en agregar al .env y usar esta variable en el servidor real
ENVIRONMENT = os.getenv("DJANGO_ENV", "development")

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Discord Webhook URL
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "product",
    "drf_spectacular",
    "rest_framework_simplejwt.token_blacklist",
    "csp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

required_vars = ["DB_ENGINE", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Variable de entorno {var} no está configurada")


DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": "verify-full",
            "sslrootcert": os.path.join(BASE_DIR, "global-bundle.pem"),
            "connect_timeout": 5,
            # CAMBIAR EL TIEMPO PARA CUANDO ESTE EN PRODUCCION (REDUCIRLO)
            "options": "-c statement_timeout=30000 -c lock_timeout=10000",
        },
    }
}

# ── Errores genéricos via DRF ──

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        [
            "rest_framework.renderers.JSONRenderer",
        ]
        if ENVIRONMENT == "production"
        else [
            "rest_framework.renderers.JSONRenderer",
            "rest_framework.renderers.BrowsableAPIRenderer",
        ]
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "product.authentication.CookieJWTAuthentication",
    ),
    "EXCEPTION_HANDLER": "product.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "2/minute",
        "user": "10/minute",
         'ip': '60/minute',       
         'login': '3/minute',
         'auth_session': '10/minute',
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

TRUSTED_PROXY = ENVIRONMENT == "production"

SPECTACULAR_SETTINGS = {
    "TITLE": "Walmart México - API de Inventario",
    "DESCRIPTION": "API REST para gestión de inventario de productos",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── Límite de tamaño ──
DATA_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024  # 1 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# CAMBIAR UNOS PUNTOS A TRUE ANTES DE PRODUCCION
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=30),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_COOKIE": "access_token",
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SECURE": True,  # SOLO en producción (HTTPS)
    "AUTH_COOKIE_SAMESITE": "Lax",
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Cookies seguras
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # necesario para frontend

CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "https://tudominio.com"]
CORS_ALLOW_CREDENTIALS = True

MIDDLEWARE.insert(0, "product.middleware.SecurityMiddleware")

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

# origins permitidos para CORS, en produccion se lee del .env
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")


# evita que el navegador adivine el tipo de archivo
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
CONTENT_SECURITY_POLICY = "frame-ancestors 'none'"


# default 'none', todo bloqueado menos lo que se especifica
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ("'none'",),
        "connect-src": ("'self'", "http://localhost:5173", "http://127.0.0.1:5173"),
        "script-src": ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"),
        "style-src": ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"),
        "img-src": ("'self'", "data:", "https://cdn.jsdelivr.net"),
        "font-src": ("'self'",),
        "frame-ancestors": ("'none'",),
        "connect-src": (
            "'self'",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://cdn.jsdelivr.net",
        ),
    }
}

# ── HTTPS y cookies seguras: solo en producción ──
# en local no hay HTTPS, activar estos settings lo rompería
if ENVIRONMENT == "production":
    # redirige HTTP → HTTPS automáticamente
    SECURE_SSL_REDIRECT = True

    # Django corre detrás de Nginx en producción
    # este header le dice a Django que la petición original era HTTPS
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # HSTS: el navegador recuerda usar solo HTTPS por 1 año
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # cookies solo viajan por HTTPS, nunca por HTTP plano
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Igual se define en el .env cuando ya este en produccion (ruta del vue)
    FRONTEND_URL = os.getenv("FRONTEND_URL", "")
    if FRONTEND_URL:
        CSP_CONNECT_SRC += (FRONTEND_URL,)
