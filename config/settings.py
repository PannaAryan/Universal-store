"""Django settings for the Dokan AI platform."""

import os
import warnings
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes", "on"}


# Vercel sets VERCEL=1 at build and run time. Its serverless filesystem is read-only
# except /tmp, and requests arrive over HTTPS through a proxy.
ON_VERCEL = bool(os.environ.get("VERCEL"))

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "dev-insecure-change-me-7c1f0b3e9a2d4f68b5e1c0a9d8f7e6b5"
)
DEBUG = env_bool("DJANGO_DEBUG", not ON_VERCEL)
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",") if h]
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]
for _var in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
    if os.environ.get(_var):
        CSRF_TRUSTED_ORIGINS.append(f"https://{os.environ[_var]}")

# Trust the proxy's scheme header so Django knows the request was HTTPS
# (otherwise the CSRF origin check rejects every form POST).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if ON_VERCEL:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "core",
    "accounts",
    "stores",
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

ROOT_URLCONF = "config.urls"

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
                "core.context_processors.brand",
                "stores.context_processors.dashboard",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Use DATABASE_URL (e.g. Neon / Vercel Postgres) when set. Without it, Vercel falls back
# to a throwaway SQLite file in /tmp that is migrated and seeded on each cold start.
_default_sqlite = "/tmp/db.sqlite3" if ON_VERCEL else BASE_DIR / "db.sqlite3"
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{_default_sqlite}", conn_max_age=60, conn_health_checks=True
    )
}
USING_EPHEMERAL_DB = ON_VERCEL and not os.environ.get("DATABASE_URL")
if USING_EPHEMERAL_DB:
    # Each serverless instance has its own /tmp database, so keep sessions in signed
    # cookies to stay logged in (and keep the cart) across instances.
    SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "accounts.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "core:home"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
# Serve static files straight from app/static dirs, so no collectstatic step is needed
# on Vercel. Harmless locally.
WHITENOISE_USE_FINDERS = True
warnings.filterwarnings("ignore", message="No directory at", module="whitenoise.base")
WHITENOISE_AUTOREFRESH = DEBUG
MEDIA_URL = "media/"
MEDIA_ROOT = Path("/tmp/media") if ON_VERCEL else BASE_DIR / "media"
SERVE_MEDIA = DEBUG or ON_VERCEL

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)

# --- Brand -----------------------------------------------------------------
BRAND = {
    "name": os.environ.get("BRAND_NAME", "Dokan AI"),
    "tagline": "Take a photo. Get a store.",
    "email": os.environ.get("BRAND_EMAIL", "hello@dokan.ai"),
    "phone": os.environ.get("BRAND_PHONE", "+880 1700-000000"),
    "address": "Gulshan 2, Dhaka 1212, Bangladesh",
    "support_hours": "7 days · 9am–11pm",
}

# --- AI listing generator ---------------------------------------------------
# When ANTHROPIC_API_KEY (or another Anthropic credential) is available, Snap & Sell
# uses Claude vision; otherwise it falls back to the built-in template writer.
AI_ENABLED = env_bool("AI_ENABLED", bool(os.environ.get("ANTHROPIC_API_KEY")))
AI_MODEL = os.environ.get("AI_MODEL", "claude-opus-5")

# --- OTP --------------------------------------------------------------------
# No SMS gateway is wired up yet, so the code is shown on screen (demo mode) or buyers
# could never finish checkout. Set OTP_SHOW_ON_SCREEN=0 once send_sms() is connected.
OTP_SHOW_ON_SCREEN = env_bool("OTP_SHOW_ON_SCREEN", True)
