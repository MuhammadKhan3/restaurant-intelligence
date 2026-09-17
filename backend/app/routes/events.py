"""Event ingestion/history routes for cv-service's table/camera/entrance/queue
events and table session records."""

from fastapi import APIRouter, Query, Request

from app.schemas.event import (
    CameraEventCreate,
    CameraEventResponse,
    EntranceEventCreate,
    EntranceEventResponse,
    QueueEventCreate,
    QueueEventResponse,
    TableEventCreate,
    TableEventResponse,
    TableSessionCreate,
    TableSessionResponse,
)
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/tables", response_model=TableEventResponse, status_code=201)
def ingest_table_event(event: TableEventCreate, request: Request) -> TableEventResponse:
    with request.app.state.session_factory() as session:
        return EventService(session).record_table_event(event)


@router.get("/tables", response_model=list[TableEventResponse])
def list_table_events(
    request: Request,
    zone_id: str | None = None,
    limit: int = Query(default=100, le=1000),
) -> list[TableEventResponse]:
    with request.app.state.session_factory() as session:
        return EventService(session).list_table_events(zone_id=zone_id, limit=limit)


@router.post("/cameras", response_model=CameraEventResponse, status_code=201)
def ingest_camera_event(event: CameraEventCreate, request: Request) -> CameraEventResponse:
    with request.app.state.session_factory() as session:
        return EventService(session).record_camera_event(event)


@router.get("/cameras", response_model=list[CameraEventResponse])
def list_camera_events(
    request: Request,
    camera_id: str | None = None,
    limit: int = Query(default=100, le=1000),
) -> list[CameraEventResponse]:
    with request.app.state.session_factory() as session:
        return EventService(session).list_camera_events(camera_id=camera_id, limit=limit)


@router.post("/entrance", response_model=EntranceEventResponse, status_code=201)
def ingest_entrance_event(event: EntranceEventCreate, request: Request) -> EntranceEventResponse:
    with request.app.state.session_factory() as session:
        return EventService(session).record_entrance_event(event)


@router.get("/entrance", response_model=list[EntranceEventResponse])
def list_entrance_events(
    request: Request,
    zone_id: str | None = None,
    limit: int = Query(default=100, le=1000),
) -> list[EntranceEventResponse]:
    with request.app.state.session_factory() as session:
        return EventService(session).list_entrance_events(zone_id=zone_id, limit=limit)


@router.post("/queue", response_model=QueueEventResponse, status_code=201)
def ingest_queue_event(event: QueueEventCreate, request: Request) -> QueueEventResponse:
    with request.app.state.session_factory() as session:
        return EventService(session).record_queue_event(event)


@router.get("/queue", response_model=list[QueueEventResponse])
def list_queue_events(
    request: Request,
    zone_id: str | None = None,
    limit: int = Query(default=100, le=1000),
) -> list[QueueEventResponse]:
    with request.app.state.session_factory() as session:
        return EventService(session).list_queue_events(zone_id=zone_id, limit=limit)


@router.post("/table-sessions", response_model=TableSessionResponse, status_code=201)
def ingest_table_session(session_data: TableSessionCreate, request: Request) -> TableSessionResponse:
    with request.app.state.session_factory() as session:
        return EventService(session).record_table_session(session_data)


@router.get("/table-sessions", response_model=list[TableSessionResponse])
def list_table_sessions(
    request: Request,
    zone_id: str | None = None,
    limit: int = Query(default=100, le=1000),
) -> list[TableSessionResponse]:
    with request.app.state.session_factory() as session:
        return EventService(session).list_table_sessions(zone_id=zone_id, limit=limit)
