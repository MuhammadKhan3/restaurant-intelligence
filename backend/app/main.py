"""Application entry point: builds and serves the backend FastAPI app."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.db import create_session_factory
from app.routes import events_router, health_router

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
    app.state.session_factory = create_session_factory(settings.database_url)

    logger.info("Restaurant Intelligence - Backend")
    logger.info("Environment: %s", settings.app_env)
    logger.info("Application started")

    yield

    logger.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(title="Restaurant Intelligence - Backend", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[get_settings().frontend_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(events_router)
    return app


app = create_app()


def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=4000)


if __name__ == "__main__":
    main()
