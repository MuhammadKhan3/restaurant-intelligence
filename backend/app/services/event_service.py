"""Persists and retrieves CV-emitted table, camera, entrance, and queue events."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import (
    CameraEvent,
    EntranceEvent,
    QueueEvent,
    TableEvent,
    TableSessionRecord,
)
from app.schemas.event import (
    CameraEventCreate,
    EntranceEventCreate,
    QueueEventCreate,
    TableEventCreate,
    TableSessionCreate,
)


class EventService:
    """CRUD over table/camera/entrance/queue events for a single request-scoped session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def record_table_event(self, event: TableEventCreate) -> TableEvent:
        record = TableEvent(
            zone_id=event.zone_id,
            from_state=event.from_state,
            to_state=event.to_state,
            occurred_at=event.occurred_at,
            received_at=datetime.now(timezone.utc),
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def list_table_events(self, zone_id: str | None = None, limit: int = 100) -> list[TableEvent]:
        query = select(TableEvent).order_by(TableEvent.occurred_at.desc()).limit(limit)
        if zone_id is not None:
            query = query.where(TableEvent.zone_id == zone_id)
        return list(self._session.execute(query).scalars())

    def record_camera_event(self, event: CameraEventCreate) -> CameraEvent:
        record = CameraEvent(
            camera_id=event.camera_id,
            status=event.status,
            occurred_at=event.occurred_at,
            received_at=datetime.now(timezone.utc),
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def list_camera_events(
        self, camera_id: str | None = None, limit: int = 100
    ) -> list[CameraEvent]:
        query = select(CameraEvent).order_by(CameraEvent.occurred_at.desc()).limit(limit)
        if camera_id is not None:
            query = query.where(CameraEvent.camera_id == camera_id)
        return list(self._session.execute(query).scalars())

    def record_entrance_event(self, event: EntranceEventCreate) -> EntranceEvent:
        record = EntranceEvent(
            zone_id=event.zone_id,
            track_id=event.track_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            received_at=datetime.now(timezone.utc),
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def list_entrance_events(
        self, zone_id: str | None = None, limit: int = 100
    ) -> list[EntranceEvent]:
        query = select(EntranceEvent).order_by(EntranceEvent.occurred_at.desc()).limit(limit)
        if zone_id is not None:
            query = query.where(EntranceEvent.zone_id == zone_id)
        return list(self._session.execute(query).scalars())

    def record_queue_event(self, event: QueueEventCreate) -> QueueEvent:
        record = QueueEvent(
            zone_id=event.zone_id,
            track_id=event.track_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            received_at=datetime.now(timezone.utc),
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def list_queue_events(self, zone_id: str | None = None, limit: int = 100) -> list[QueueEvent]:
        query = select(QueueEvent).order_by(QueueEvent.occurred_at.desc()).limit(limit)
        if zone_id is not None:
            query = query.where(QueueEvent.zone_id == zone_id)
        return list(self._session.execute(query).scalars())

    def record_table_session(self, session: TableSessionCreate) -> TableSessionRecord:
        record = TableSessionRecord(
            zone_id=session.zone_id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            peak_customer_count=session.peak_customer_count,
            status=session.status,
            received_at=datetime.now(timezone.utc),
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def list_table_sessions(
        self, zone_id: str | None = None, limit: int = 100
    ) -> list[TableSessionRecord]:
        query = select(TableSessionRecord).order_by(TableSessionRecord.started_at.desc()).limit(limit)
        if zone_id is not None:
            query = query.where(TableSessionRecord.zone_id == zone_id)
        return list(self._session.execute(query).scalars())
