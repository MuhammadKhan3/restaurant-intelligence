"""Database engine/session setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    """Build a session factory for `database_url`, creating tables if needed.

    SQLite URLs get a `StaticPool` so an in-memory database (used in tests)
    stays alive and consistent across the threadpool FastAPI runs sync routes on.
    """
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    else:
        engine = create_engine(database_url)

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
