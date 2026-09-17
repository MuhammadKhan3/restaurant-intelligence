"""Basic smoke tests for application configuration and the FastAPI app."""

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app, create_app


def test_settings_load_with_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "restaurant-intelligence"
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"


def test_get_settings_returns_settings_instance() -> None:
    settings = get_settings()

    assert isinstance(settings, Settings)


def test_create_app_builds_fastapi_instance() -> None:
    created_app = create_app()

    assert created_app.title == "Restaurant Intelligence - CV Service"


def test_app_starts_without_errors() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
