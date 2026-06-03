import os
from pathlib import Path

from .config import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Load from environment variable; fallback only for local development.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure--CHANGE_ME-IN-PRODUCTION--73hy!ksrvt0mp010hj")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "channels",
    "rest_framework",
    "drf_spectacular",
    "project",
    "users",
    "order",
    "webshell",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "utils.common.GlobalUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Kael.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Fixed typo: was "kaer", project name is "Kael"
WSGI_APPLICATION = "Kael.wsgi.application"
ASGI_APPLICATION = "Kael.asgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": [
            f"redis://{item.split(':')[0]}:{item.split(':')[1]}" for item in config.SENTRY_HOST.split(",") if item
        ]
        if config.SENTRY_HOST
        else f"redis://127.0.0.1:6379/{config.REDIS_DB}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.SentinelClient",
            "CONNECTION_FACTORY": "django_redis.pool.SentinelConnectionFactory",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 20,
                "decode_responses": True,
                "service_name": config.SERVICE_NAME,
            },
            "SENTINELS": [
                (item.split(":")[0], int(item.split(":")[1])) for item in config.SENTRY_HOST.split(",") if item
            ]
            if config.SENTRY_HOST
            else [],
            "SENTINEL_KWARGS": {"password": config.SENTRY_PASSWORD},
            "PASSWORD": config.REDIS_PASSWORD,
        },
    }
}

# Fallback to local cache if Redis is not configured
if not config.SENTRY_HOST:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }


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


LANGUAGE_CODE = "zh-hans"

TIME_ZONE = "Asia/Shanghai"

USE_I18N = True

USE_TZ = False


STATIC_URL = "/static/"

# DRF configuration
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "utils.pagination.StandardPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# drf-spectacular API schema settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Kael CMDB API",
    "DESCRIPTION": "CMDB management system API documentation",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# CORS & CSRF Settings for Front-end Session Authentication Integration
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True  # For dev environments. In production, configure CORS_ALLOWED_ORIGINS.

# Trust the frontend origins for CSRF validation (Django 4.0+)
CSRF_TRUSTED_ORIGINS = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:5173").split(",")
