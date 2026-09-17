"""Data model for an operational alert."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class AlertType(StrEnum):
    LONG_QUEUE = "long_queue"
    LONG_WAIT = "long_wait"
    LONG_OCCUPANCY = "long_occupancy"
    CAMERA_OFFLINE = "camera_offline"
    UNKNOWN_TABLE = "unknown_table"


@dataclass
class Alert:
    """A single raised alert.

    `subject_id` is whatever the alert is about — a table/queue zone id or a
    camera id — kept generic since alerts span several kinds of entities.
    """

    id: str
    alert_type: AlertType
    subject_id: str
    message: str
    raised_at: datetime
    acknowledged: bool = field(default=False)
    acknowledged_at: datetime | None = None
