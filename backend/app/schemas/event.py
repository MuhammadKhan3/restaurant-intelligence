"""Request/response schemas for the event ingestion API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TableEventCreate(BaseModel):
    """A table state transition reported by cv-service."""

    zone_id: str
    from_state: str
    to_state: str
    occurred_at: datetime


class TableEventResponse(TableEventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    received_at: datetime


class CameraEventCreate(BaseModel):
    """A camera connection status change reported by cv-service."""

    camera_id: str
    status: str
    occurred_at: datetime


class CameraEventResponse(CameraEventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    received_at: datetime


class EntranceEventCreate(BaseModel):
    """An entry/exit crossing reported by cv-service."""

    zone_id: str
    track_id: int
    event_type: str
    occurred_at: datetime


class EntranceEventResponse(EntranceEventCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    received_at: datetime
