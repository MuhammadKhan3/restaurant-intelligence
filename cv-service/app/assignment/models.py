"""Data model for a group's assignment to a table."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class AssignmentStatus(StrEnum):
    """Lifecycle of a group's assignment to a table."""

    WALKING = "walking"
    SEATED = "seated"


@dataclass
class TableAssignment:
    """A waiting group matched to a table, from assignment through seating.

    Creation of this record is itself the "assignment event" — `zone_id`,
    `track_ids`, and `assigned_at` are its payload.
    """

    zone_id: str
    track_ids: list[int]
    assigned_at: datetime
    status: AssignmentStatus = field(default=AssignmentStatus.WALKING)
    seated_at: datetime | None = None
