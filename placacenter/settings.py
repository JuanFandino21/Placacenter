from pathlib import Path
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qsl

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga variables desde .env en local (en Railway se leen del entorno)
load_dotenv(BASE_DIR / ".env", override=True)

# --- Seguridad / Debug ---
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-placacenter")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

# --- Hosts / CSRF ---
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]

_raw_csrf = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").strip()
if _raw_csrf:
    CSRF_TRUSTED_ORIGINS = [u.strip() for u in _raw_csrf.split(",") if u.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h not in ("*", "", "localhost", "127.0.0.1")]
    if DEBUG:
        CSRF_TRUSTED_ORIGINS += ["http://localhost", "http://127.0.0.1"]

# Detrás del proxy de Railway
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# --- Apps ---
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

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

WSGI_APPLICATION = "placacenter.wsgi.application"
ASGI_APPLICATION = "placacenter.asgi.application"

# --- Base de Datos: PostgreSQL (Railway). SIN SQLite ---
def parse_database_url(url: str):
    r = urlparse(url)
    scheme = (r.scheme or "").lower()

    if scheme not in ("postgres", "postgresql"):
        raise RuntimeError(f"Solo soportamos PostgreSQL. Esquema recibido: {scheme or '(vacío)'}")

    engine = "django.db.backends.postgresql"
    default_port = 5432

    cfg = {
        "ENGINE": engine,
        "NAME": (r.path or "").lstrip("/"),
        "USER": r.username,
        "PASSWORD": r.password,
        "HOST": r.hostname,
        "PORT": r.port or default_port,
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),  # pooling simple
        "CONN_HEALTH_CHECKS": True,
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "OPTIONS": {
            # Tiempo de espera para conectar; evita cuelgues cuando el proxy está dormido
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
        },
    }

    # Mezclar parámetros de query (ej. sslmode=require) en OPTIONS
    qparams = dict(parse_qsl(r.query or ""))
    if qparams:
        cfg["OPTIONS"].update(qparams)

    # Forzar sslmode=require si no vino en la URL
    if "sslmode" not in cfg["OPTIONS"]:
        cfg["OPTIONS"]["sslmode"] = "require"

    return cfg


def build_cfg_from_env():
    """Permite configurar sin DATABASE_URL usando PG* envs (Railway)."""
    host = os.getenv("PGHOST")
    name = os.getenv("PGNAME") or os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB")
    user = os.getenv("PGUSER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD")
    port = os.getenv("PGPORT")
    sslmode = os.getenv("PGSSLMODE", "require")

    required = [host, name, user, password]
    if not all(required):
        return None

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": int(port) if port else 5432,
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "OPTIONS": {
            "sslmode": sslmode,
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
        },
    }


DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DB_DEFAULT = parse_database_url(DATABASE_URL)
else:
    # Si no hay DATABASE_URL, intenta con PG* (Railway variables separadas)
    cfg = build_cfg_from_env()
    if not cfg:
        raise RuntimeError(
            "Config DB inválida: define DATABASE_URL o las variables PGHOST, PGPORT, PGUSER, PGPASSWORD y PGNAME."
        )
    DB_DEFAULT = cfg

DATABASES = {"default": DB_DEFAULT}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# --- Static / Whitenoise ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- DRF ---
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ]
}

# --- Auth / Login ---
LOGIN_URL = "/signin/"
LOGIN_REDIRECT_URL = "/principal/"
LOGOUT_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

# --- Auth0 (desde .env) ---
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")
AUTH0_CALLBACK_URL = os.getenv("AUTH0_CALLBACK_URL", "")
AUTH0_LOGOUT_REDIRECT = os.getenv("AUTH0_LOGOUT_REDIRECT", LOGOUT_REDIRECT_URL)
