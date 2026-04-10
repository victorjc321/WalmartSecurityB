from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv
from corsheaders.defaults import default_headers

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

ENVIRONMENT = os.getenv("DJANGO_ENV", "development")

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

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
    "product.middleware.SecurityMiddleware",
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
            "sslmode": "require",
            "sslrootcert": os.path.join(BASE_DIR, "global-bundle.pem"),
            "connect_timeout": 5,
            "options": f"-c statement_timeout={os.getenv('DB_STATEMENT_TIMEOUT', '30000')} "
            f"-c lock_timeout={os.getenv('DB_LOCK_TIMEOUT', '10000')}",
        },
    }
}


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
        "anon": "10/minute",
        "user": "30/minute",
        "ip": "20/minute",
        "login": "5/minute",
        "auth_session": "15/minute",
        "supplier_create": "10/hour",
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

DATA_UPLOAD_MAX_MEMORY_SIZE = 1 * 1024 * 1024
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

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=6),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_COOKIE": "access_token",
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SECURE": ENVIRONMENT == "production",
    "AUTH_COOKIE_SAMESITE": "None",
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_ENGINE = "django.contrib.sessions.backends.db"
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://walmartsecurityf1.pages.dev,https://api.nextsparktech.website",
).split(",")
CORS_ALLOW_CREDENTIALS = True


CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-critical-token",
]

MIDDLEWARE.insert(0, "product.middleware.SecurityMiddleware")

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "https://walmartsecurityf1.pages.dev",
).split(",")


SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_RESOURCE_POLICY = "same-origin"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ("'none'",),
        "script-src": (
            "'self'",
            "https://cdn.jsdelivr.net",
            "https://challenges.cloudflare.com",
            "'unsafe-inline'",
        ),
        "style-src": (
            "'self'",
            "https://cdn.jsdelivr.net",
            "'unsafe-inline'",
        ),
        "img-src": ("'self'", "data:", "https://cdn.jsdelivr.net"),
        "font-src": ("'self'",),
        "frame-src": (
            "'self'",
            "https://challenges.cloudflare.com",
            "https://*.cloudflare.com",
        ),
        "frame-ancestors": ("'none'",),
        "connect-src": (
            "'self'",
            "https://api.nextsparktech.website",
            "https://walmartsecurityf1.pages.dev",
            "https://challenges.cloudflare.com",
        ),
    }
}


if ENVIRONMENT == "production":
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"

    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    FRONTEND_URL = os.getenv("FRONTEND_URL", "")
    CONTENT_SECURITY_POLICY["DIRECTIVES"]["connect-src"] = (
        "'self'",
        "https://challenges.cloudflare.com",
        "https://api.nextsparktech.website",
        *((FRONTEND_URL,) if FRONTEND_URL else ()),
    )
