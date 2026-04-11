# from pathlib import Path
# from datetime import timedelta
# import environ 
# import os

# BASE_DIR = Path(__file__).resolve().parent.parent

# # =======================
# # ENV CONFIG
# # =======================
# env = environ.Env(
#     DEBUG=(bool, False)
# )

# environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# SECRET_KEY = env("SECRET_KEY")
# DEBUG = env("DEBUG")

# ALLOWED_HOSTS = ["*"]

# CSRF_TRUSTED_ORIGINS = [
#     "https://local-mart-11yd.onrender.com"
# ]

# # =======================
# # APPS
# # =======================
# INSTALLED_APPS = [
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "cloudinary", "cloudinary_storage",

#     "rest_framework",
#     "django_filters",
#     "corsheaders",

#     "users",
#     "products",
#     "orders",
#     "reviews",
#     "specialOffer",
#     "dashboard",
#     "payments",
#     "cart",
#     "category",
# ]
# DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
# CLOUDINARY_STORAGE = {
#     "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME"),
#     "API_KEY": env("CLOUDINARY_API_KEY"),
#     "API_SECRET": env("CLOUDINARY_API_SECRET"),
# }

# AUTH_USER_MODEL = "users.User"
# ROOT_URLCONF = "localmart_backend.urls"


# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]


# # =======================
# # MIDDLEWARE
# # =======================
# MIDDLEWARE = [
#     "corsheaders.middleware.CorsMiddleware",
#     "django.middleware.security.SecurityMiddleware",
#     'whitenoise.middleware.WhiteNoiseMiddleware',
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
# ]

# # =======================
# # CORS (LOCAL)
# # =======================
# CORS_ALLOW_ALL_ORIGINS = True

# # =======================
# # DRF
# # =======================
# REST_FRAMEWORK = {
#     "DEFAULT_AUTHENTICATION_CLASSES": (
#         "rest_framework_simplejwt.authentication.JWTAuthentication",
#     ),
#     "DEFAULT_PERMISSION_CLASSES": (
#         "rest_framework.permissions.AllowAny",
#     ),
# }

# SIMPLE_JWT = {
#     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
#     "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
# }

# # =======================
# # DATABASE (SQLite ONLY)
# # =======================
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

# # =======================
# # STATIC & MEDIA
# # =======================
# STATIC_URL = "/static/"
# MEDIA_URL = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"
# STATIC_ROOT = BASE_DIR / "staticfiles"
# STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# # =======================
# # STRIPE
# # =======================
# STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
# STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY")

# # =======================
# # CUSTOM
# # =======================
# BACKEND_BASE_URL = env("BACKEND_BASE_URL")

# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"



from pathlib import Path
from datetime import timedelta
import environ
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# =======================
# ENV CONFIG
# =======================
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://local-mart-11yd.onrender.com"
]

# =======================
# APPS
# =======================
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

# =======================
# MIDDLEWARE
# =======================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # must be right after security
    "corsheaders.middleware.CorsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =======================
# TEMPLATES
# =======================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # IMPORTANT
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

ROOT_URLCONF = "localmart_backend.urls"

# =======================
# DATABASE
# =======================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# =======================
# STATIC FILES (FIXED)
# =======================
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # 🔥 VERY IMPORTANT
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# =======================
# MEDIA (Cloudinary)
# =======================
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": env("CLOUDINARY_CLOUD_NAME"),
    "API_KEY": env("CLOUDINARY_API_KEY"),
    "API_SECRET": env("CLOUDINARY_API_SECRET"),
}

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# =======================
# CORS
# =======================
CORS_ALLOW_ALL_ORIGINS = True

# =======================
# DRF
# =======================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# =======================
# STRIPE
# =======================
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY")

# =======================
# CUSTOM
# =======================
BACKEND_BASE_URL = env("BACKEND_BASE_URL")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"