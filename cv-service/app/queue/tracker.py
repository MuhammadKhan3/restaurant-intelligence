"""Queue entry/exit detection: tracks each person's presence in the queue zone."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.queue.models import QueueZone
from app.tables.occupancy import person_center_point, point_in_polygon
from app.tables.state import utc_now
from app.tracking.types import Track

Clock = Callable[[], datetime]


class QueueEventType(StrEnum):
    ENTRY = "entry"
    EXIT = "exit"


@dataclass(frozen=True)
class QueueEvent:
    """A single detected join/leave of the queue zone."""

    zone_id: str
    track_id: int
    event_type: QueueEventType
    timestamp: datetime


class QueueTracker:
    """Tracks who is currently waiting in `zone` and emits join/leave events.

    A track whose center point enters the polygon fires ENTRY; leaving it (or
    being explicitly removed via `remove_track`, e.g. once tracking has lost it
    for good) fires EXIT. `current_count` is the number of people currently
    waiting.
    """

    def __init__(self, zone: QueueZone, clock: Clock = utc_now) -> None:
        self._zone = zone
        self._clock = clock
        self._in_queue: set[int] = set()

    def update(self, tracks: list[Track]) -> list[QueueEvent]:
        events: list[QueueEvent] = []

        for track in tracks:
            center = person_center_point(track.bbox)
            in_zone = point_in_polygon(center, self._zone.points)
            currently_counted = track.track_id in self._in_queue

            if in_zone and not currently_counted:
                self._in_queue.add(track.track_id)
                events.append(self._event(track.track_id, QueueEventType.ENTRY))
            elif not in_zone and currently_counted:
                self._in_queue.discard(track.track_id)
                events.append(self._event(track.track_id, QueueEventType.EXIT))

        return events

    def remove_track(self, track_id: int) -> QueueEvent | None:
        """Force an EXIT for a track that tracking has permanently lost.

        Without this, a track that vanishes (rather than visibly walking out of
        the zone) would stay counted as waiting forever.
        """
        if track_id not in self._in_queue:
            return None
        self._in_queue.discard(track_id)
        return self._event(track_id, QueueEventType.EXIT)

    def _event(self, track_id: int, event_type: QueueEventType) -> QueueEvent:
        return QueueEvent(
            zone_id=self._zone.id, track_id=track_id, event_type=event_type, timestamp=self._clock()
        )

    @property
    def current_count(self) -> int:
        return len(self._in_queue)
