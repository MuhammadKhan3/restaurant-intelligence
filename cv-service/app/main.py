"""Application entry point: builds and serves the FastAPI app."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.config import Settings, get_settings
from app.detection.factory import create_person_detector
from app.routes import detection_router, health_router

logger = logging.getLogger(__name__)


def configure_logging(log_level: str) -> None:
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings: Settings = get_settings()
    configure_logging(settings.log_level)

    app.state.settings = settings
    app.state.person_detector = create_person_detector(settings)

    logger.info("Restaurant Intelligence")
    logger.info("Environment: %s", settings.app_env)
    logger.info("Application started")

    yield

    logger.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(title="Restaurant Intelligence - CV Service", lifespan=lifespan)
    app.include_router(health_router)
    app.include_router(detection_router)
    return app


app = create_app()


def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
