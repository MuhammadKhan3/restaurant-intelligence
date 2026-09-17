"""ORM models for CV-emitted events."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TableEvent(Base):
    """A recorded table state transition, as emitted by cv-service."""

    __tablename__ = "table_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String, index=True)
    from_state: Mapped[str] = mapped_column(String)
    to_state: Mapped[str] = mapped_column(String)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CameraEvent(Base):
    """A recorded camera connection status change, as emitted by cv-service."""

    __tablename__ = "camera_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    camera_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EntranceEvent(Base):
    """A recorded entry/exit crossing, as emitted by cv-service."""

    __tablename__ = "entrance_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String, index=True)
    track_id: Mapped[int] = mapped_column()
    event_type: Mapped[str] = mapped_column(String)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class QueueEvent(Base):
    """A recorded queue join/leave event, as emitted by cv-service."""

    __tablename__ = "queue_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String, index=True)
    track_id: Mapped[int] = mapped_column()
    event_type: Mapped[str] = mapped_column(String)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TableSessionRecord(Base):
    """A continuous anonymous customer dining session, as tracked by cv-service's
    `TableSessionTracker`. No personally-identifying data -- `peak_customer_count`
    is a headcount, never an identity.
    """

    __tablename__ = "table_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    peak_customer_count: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
