"""Event ingestion and history routes for table/camera/entrance events emitted by cv-service."""

from fastapi import APIRouter, Query, Request

from app.schemas.event import (
    CameraEventCreate,
    CameraEventResponse,
    EntranceEventCreate,
    EntranceEventResponse,
    TableEventCreate,
    TableEventResponse,
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
