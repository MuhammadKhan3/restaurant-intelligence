"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "restaurant-intelligence"
    app_env: str = "development"
    log_level: str = "INFO"

    video_source_type: str = "video"
    video_source: str = ""

    yolo_model: str = "yolov8n.pt"
    confidence_threshold: float = 0.4

    table_zones_file: str = "table_zones.json"
    occupancy_threshold: int = 1

    backend_url: str = "http://localhost:4000"


def get_settings() -> Settings:
    """Return a fresh Settings instance loaded from the environment."""
    return Settings()
