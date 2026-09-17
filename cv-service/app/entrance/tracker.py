"""Entry/exit detection: tracks each person's side of the entrance zone across frames."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.entrance.models import EntranceZone
from app.tables.occupancy import person_center_point, point_in_polygon
from app.tables.state import utc_now
from app.tracking.types import Track

Clock = Callable[[], datetime]

_Side = str  # "outside" | "inside"


class EntranceEventType(StrEnum):
    ENTRY = "entry"
    EXIT = "exit"


@dataclass(frozen=True)
class EntranceEvent:
    """A single detected crossing of the entrance zone."""

    zone_id: str
    track_id: int
    event_type: EntranceEventType
    timestamp: datetime


class EntranceTracker:
    """Detects entry/exit events by watching which side of `zone` each track is on.

    A track moving from the outside polygon to the inside polygon between two
    `update()` calls is an ENTRY; the reverse is an EXIT. A track with no prior
    known side (first sighting) never fires an event on that first sighting —
    there is nothing to compare against yet.
    """

    def __init__(self, zone: EntranceZone, clock: Clock = utc_now) -> None:
        self._zone = zone
        self._clock = clock
        self._last_side: dict[int, _Side] = {}

    def _side_of(self, track: Track) -> _Side | None:
        center = person_center_point(track.bbox)
        if point_in_polygon(center, self._zone.inside_points):
            return "inside"
        if point_in_polygon(center, self._zone.outside_points):
            return "outside"
        return None

    def update(self, tracks: list[Track]) -> list[EntranceEvent]:
        events: list[EntranceEvent] = []

        for track in tracks:
            side = self._side_of(track)
            if side is None:
                continue

            previous_side = self._last_side.get(track.track_id)
            self._last_side[track.track_id] = side

            if previous_side is None or previous_side == side:
                continue

            event_type = EntranceEventType.ENTRY if side == "inside" else EntranceEventType.EXIT
            events.append(
                EntranceEvent(
                    zone_id=self._zone.id,
                    track_id=track.track_id,
                    event_type=event_type,
                    timestamp=self._clock(),
                )
            )

        return events
