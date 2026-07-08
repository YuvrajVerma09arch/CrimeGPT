"""Application settings loaded from environment / .env file."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"

    # Database — SQLite by default so the demo runs with zero external services
    database_url: str = "sqlite+aiosqlite:///./crimegpt.db"

    # Auth
    jwt_secret: str = "dev-only-secret-change-me-in-production-min32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # AI / RAG
    openai_api_key: str = ""
    chroma_db_path: str = "./chroma_db"

    # Translation
    translation_service_url: str = ""
    google_translate_api_key: str = ""

    # Storage
    upload_dir: str = "./uploads"

    # Celery / Redis
    redis_url: str = "redis://localhost:6379"
    use_celery: bool = False

    # OCR
    google_vision_api_key: str = ""

    # CORS
    allowed_origins: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
