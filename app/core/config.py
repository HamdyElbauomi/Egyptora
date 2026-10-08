"""App settings, read from environment variables or the .env file.

Owner: Person 1 (shared — ask before changing).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Egyptora API"
    environment: str = "dev"  # dev | test | prod

    database_url: str = "postgresql+psycopg://egyptora:egyptora@localhost:5433/egyptora"
    # Read-only user for running AI-generated SQL (Person 5). Falls back to the main URL in dev.
    readonly_database_url: str | None = None

    jwt_secret: str = "dev-only-secret-change-me-in-.env-0123456789"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14

    # When true, every AI function returns fixed sample data instead of calling a model.
    ai_mock: bool = True
    # Exposes /ai/* routes in Swagger so AI owners can test their piece directly.
    expose_ai_routes: bool = True
    llm_api_key: str | None = None
    scan_confidence_threshold: float = 0.6

    upload_dir: str = "uploads"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
