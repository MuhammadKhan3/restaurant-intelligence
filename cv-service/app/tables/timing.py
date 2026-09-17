"""Table occupancy timing: session start/end, duration, and long-occupancy detection."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.tables.state import Clock, StateChange, TableState, utc_now


@dataclass
class TableSession:
    """A single continuous occupied period for a table zone."""

    zone_id: str
    start_time: datetime
    end_time: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.end_time is None

    def duration(self, now: datetime | None = None) -> timedelta:
        """Return the session length. An open session requires `now`."""
        end = self.end_time if self.end_time is not None else now
        if end is None:
            raise ValueError("session is still open; pass `now` to compute an in-progress duration")
        return end - self.start_time


class TableTimingTracker:
    """Opens/closes `TableSession`s off of `TableStateManager` state changes.

    A session starts when a zone transitions into OCCUPIED and ends when it
    transitions out of OCCUPIED (to AVAILABLE, CLEANING, BLOCKED, or UNKNOWN).
    """

    def __init__(self, clock: Clock = utc_now) -> None:
        self._clock = clock
        self._current: dict[str, TableSession] = {}
        self._history: dict[str, list[TableSession]] = {}

    def record_state_change(self, change: StateChange) -> None:
        if change.to_state == TableState.OCCUPIED:
            if change.zone_id not in self._current:
                self._current[change.zone_id] = TableSession(
                    zone_id=change.zone_id, start_time=change.timestamp
                )
        elif change.from_state == TableState.OCCUPIED:
            session = self._current.pop(change.zone_id, None)
            if session is not None:
                session.end_time = change.timestamp
                self._history.setdefault(change.zone_id, []).append(session)

    def current_session(self, zone_id: str) -> TableSession | None:
        return self._current.get(zone_id)

    def history(self, zone_id: str) -> list[TableSession]:
        return list(self._history.get(zone_id, []))

    def is_long_occupancy(self, zone_id: str, threshold: timedelta) -> bool:
        """True if the zone's current open session has exceeded `threshold`."""
        session = self._current.get(zone_id)
        if session is None:
            return False
        return session.duration(self._clock()) > threshold
