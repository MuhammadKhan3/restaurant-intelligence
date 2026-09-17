"""Data model for a table's continuous, anonymous customer dining session."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class CustomerSession:
    """One continuous dining session: an anonymous group of customers at a table.

    `track_ids` accumulates every anonymous tracker id that was ever part of
    this group while the session was active, including through brief
    occlusion -- it answers "who has been part of this visit," not just "who
    is visible this instant" (see `TableSessionTracker.current_customer_count`
    for the live count). No name, face, or other personally-identifying data
    is ever attached to a session -- `track_ids` are anonymous, ephemeral
    tracker ids that are meaningless outside this one visit.
    """

    zone_id: str
    started_at: datetime
    track_ids: frozenset[int] = field(default_factory=frozenset)
    peak_customer_count: int = 0
    status: SessionStatus = field(default=SessionStatus.ACTIVE)
    ended_at: datetime | None = None

    def duration(self, now: datetime | None = None) -> timedelta:
        """Return how long this session has lasted. An active session requires `now`."""
        end = self.ended_at if self.ended_at is not None else now
        if end is None:
            raise ValueError(
                "session is still active; pass `now` to compute an in-progress duration"
            )
        return end - self.started_at

    @property
    def is_active(self) -> bool:
        return self.status == SessionStatus.ACTIVE
