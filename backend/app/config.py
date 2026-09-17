"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "restaurant-intelligence-backend"
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/restaurant_intelligence"
    frontend_origin: str = "http://localhost:3000"


def get_settings() -> Settings:
    """Return a fresh Settings instance loaded from the environment."""
    return Settings()
