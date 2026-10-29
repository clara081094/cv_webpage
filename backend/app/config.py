import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://website:website@localhost:5433/website",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "30"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "14"))
    )

    CORS_ORIGINS = _csv(os.getenv("CORS_ORIGINS", "http://localhost:5173"))

    UPLOAD_FOLDER = str(BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024)))
    PUBLIC_MEDIA_URL = os.getenv("PUBLIC_MEDIA_URL", "/static/uploads")
    ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}

    DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE", "es")
    SUPPORTED_LOCALES = _csv(os.getenv("SUPPORTED_LOCALES", "es,en"))

    API_PREFIX = "/api/v1"
    JSON_SORT_KEYS = False
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://website:website@localhost:5433/website_test",
    )
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False

    # Placeholders from config defaults, docker-compose.yml and .env.example.
    PLACEHOLDER_SECRETS = {"dev-secret-change-me", "change-me", "change-me-too"}

    @classmethod
    def check_secrets(cls) -> None:
        """Refuse to boot with a guessable key: it would let anyone mint admin JWTs."""
        for name in ("SECRET_KEY", "JWT_SECRET_KEY"):
            value = getattr(cls, name)
            if value in cls.PLACEHOLDER_SECRETS or len(value) < 32:
                raise RuntimeError(
                    f"{name} must be set to a random value of 32+ characters"
                )


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def resolve_config(name: str | None = None):
    key = name or os.getenv("FLASK_ENV", "development")
    return CONFIGS.get(key, DevelopmentConfig)
