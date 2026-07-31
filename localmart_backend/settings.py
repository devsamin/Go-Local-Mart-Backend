"""Django settings for Local Mart.

Production values are read from environment variables. Safe local-development
defaults are intentionally narrow so a missing variable cannot silently expose
the API to every host or origin.
"""

from datetime import timedelta
from pathlib import Path
import sys

import environ
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
TESTING = "test" in sys.argv
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env.bool("DEBUG", default=False)
IS_RENDER = env.bool("RENDER", default=False)
if IS_RENDER and DEBUG and not TESTING:
    raise ImproperlyConfigured(
        "DEBUG must be False on Render. Debug responses expose internal settings "
        "and indicate that the production environment is misconfigured."
    )
SECRET_KEY = env("SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "local-development-key-change-me"
    else:
        raise ImproperlyConfigured("SECRET_KEY must be configured when DEBUG is false.")
configured_allowed_hosts = env.list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "local-mart-11yd.onrender.com"],
)
ALLOWED_HOSTS = list(
    dict.fromkeys([*configured_allowed_hosts, "local-mart-11yd.onrender.com"])
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary",
    "cloudinary_storage",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "users",
    "products",
    "orders",
    "reviews",
    "specialOffer",
    "dashboard",
    "payments",
    "cart",
    "category",
]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "localmart_backend.urls"
WSGI_APPLICATION = "localmart_backend.wsgi.application"
ASGI_APPLICATION = "localmart_backend.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
if IS_RENDER and not TESTING and DATABASES["default"]["ENGINE"].endswith("sqlite3"):
    raise ImproperlyConfigured(
        "Render must use a persistent PostgreSQL database. Set DATABASE_URL to the "
        "internal connection string of a Render Postgres instance; SQLite files on "
        "Render are ephemeral and lose runtime data after a restart or spin-down."
    )

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="Asia/Dhaka")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

cloudinary_values = {
    "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME", default="").strip(),
    "API_KEY": env("CLOUDINARY_API_KEY", default="").strip(),
    "API_SECRET": env("CLOUDINARY_API_SECRET", default="").strip(),
}
CLOUDINARY_URL = env("CLOUDINARY_URL", default="").strip()
has_cloudinary_credentials = bool(CLOUDINARY_URL) or all(cloudinary_values.values())
# Local development does not depend on an external upload service. Render sets
# RENDER=true automatically and may never opt out of persistent media storage;
# other production hosts can enable it explicitly.
USE_CLOUDINARY = (IS_RENDER and not TESTING) or env.bool(
    "USE_CLOUDINARY",
    default=False,
)
SERVE_LOCAL_MEDIA = env.bool(
    "SERVE_LOCAL_MEDIA",
    # The repository contains legacy media referenced by the production
    # database. Keep those files reachable on Render while all new uploads
    # continue to go to Cloudinary.
    default=IS_RENDER and not TESTING,
)
if USE_CLOUDINARY:
    if not has_cloudinary_credentials:
        raise ImproperlyConfigured(
            "Persistent media storage is required in production. Set CLOUDINARY_URL or "
            "all of CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET. "
            "Local uploads on Render disappear after a restart or spin-down."
        )
    if all(cloudinary_values.values()):
        CLOUDINARY_STORAGE = cloudinary_values
    STORAGES["default"] = {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"
    }

PRODUCTION_FRONTEND_URL = "https://golocalmart.vercel.app"
PRODUCTION_BACKEND_URL = "https://local-mart-11yd.onrender.com"
FRONTEND_URL = env(
    "FRONTEND_URL",
    default=PRODUCTION_FRONTEND_URL if IS_RENDER else "http://localhost:5173",
).rstrip("/")
BACKEND_BASE_URL = env(
    "BACKEND_BASE_URL",
    default=PRODUCTION_BACKEND_URL if IS_RENDER else "http://localhost:8000",
).rstrip("/")
configured_cors_origins = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[FRONTEND_URL],
)
CORS_ALLOWED_ORIGINS = list(
    dict.fromkeys([*configured_cors_origins, PRODUCTION_FRONTEND_URL])
)
configured_csrf_origins = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=CORS_ALLOWED_ORIGINS,
)
CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys([*configured_csrf_origins, PRODUCTION_FRONTEND_URL])
)
CORS_ALLOW_CREDENTIALS = False

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 24,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {"anon": "120/min", "user": "600/min"},
    "EXCEPTION_HANDLER": "localmart_backend.exceptions.api_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_CURRENCY = env("STRIPE_CURRENCY", default="bdt")
if IS_RENDER and not TESTING and (not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET):
    raise ImproperlyConfigured(
        "Stripe payments require both STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET on Render. "
        "Without the signed webhook, completed orders can remain hidden from sellers."
    )

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG) and not DEBUG and not TESTING
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0 if DEBUG else 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if TESTING:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
