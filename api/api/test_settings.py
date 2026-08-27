"""Self-contained settings for fast unit tests without external services."""

import os

from .config import Config

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENCRYPTION_KEY", "CqjV_Vna_IjUSn_GAWw-WtFDmF0aPNl0t9r4ErsGAuQ=")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,testserver")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("TIME_ZONE", "UTC")
os.environ.setdefault("CELERY_TIMEZONE", "UTC")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:5173")

# Detection binaries are mocked by unit tests and must not be a test bootstrap dependency.
Config.require_executable = staticmethod(lambda _name: None)

from .settings import *  # noqa: E402,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",  # noqa: F405
    }
}

CELERY_TASK_ALWAYS_EAGER = True
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
