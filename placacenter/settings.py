# placacenter/settings.py
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ===== Seguridad / Entorno =====
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-placacenter")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

# ALLOWED_HOSTS separados por coma (ej: "miapp.up.railway.app,otra.com")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]

# CSRF_TRUSTED_ORIGINS:
# - Si defines DJANGO_CSRF_TRUSTED_ORIGINS (urls con http/https), lo usamos.
# - Si no, lo derivamos de ALLOWED_HOSTS (https://<host>), ignorando '*'.
_raw_csrf = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").strip()
if _raw_csrf:
    CSRF_TRUSTED_ORIGINS = [u.strip() for u in _raw_csrf.split(",") if u.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h not in ("*", "", "localhost", "127.0.0.1")]
    # en dev también confiamos en http://localhost y 127.0.0.1
    if DEBUG:
        CSRF_TRUSTED_ORIGINS += ["http://localhost", "http://127.0.0.1"]

# Detrás del proxy/HTTPS de Railway
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# ===== Apps =====
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "core",
]

# ===== Middleware =====
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # estáticos en prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "placacenter.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # templates dentro de apps
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

WSGI_APPLICATION = "placacenter.wsgi.application"
ASGI_APPLICATION = "placacenter.asgi.application"

# ===== Base de datos (SQLite para demo) =====
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

# ===== I18N =====
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ===== Estáticos (WhiteNoise) =====
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===== DRF =====
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ]
}
