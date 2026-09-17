"""Queue wait timing: per-person wait duration, average/max wait, abandoned waits."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.queue.tracker import QueueEvent, QueueEventType


@dataclass
class QueueWait:
    """One person's continuous time spent waiting in a queue zone."""

    zone_id: str
    track_id: int
    entry_time: datetime
    exit_time: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.exit_time is None

    def duration(self, now: datetime | None = None) -> timedelta:
        """Return how long this wait has lasted. An open wait requires `now`."""
        end = self.exit_time if self.exit_time is not None else now
        if end is None:
            raise ValueError("wait is still open; pass `now` to compute an in-progress duration")
        return end - self.entry_time


class QueueTimingTracker:
    """Opens/closes `QueueWait`s off of `QueueEvent`s and summarizes wait times.

    "Abandoned" here means a completed wait (the person left the queue) whose
    duration exceeded a threshold — a proxy for "gave up rather than got
    seated," since this tracker alone has no signal about whether they were
    actually seated.
    """

    def __init__(self) -> None:
        self._current: dict[int, QueueWait] = {}
        self._history: list[QueueWait] = []

    def record_event(self, event: QueueEvent) -> None:
        if event.event_type == QueueEventType.ENTRY:
            if event.track_id not in self._current:
                self._current[event.track_id] = QueueWait(
                    zone_id=event.zone_id, track_id=event.track_id, entry_time=event.timestamp
                )
        elif event.event_type == QueueEventType.EXIT:
            wait = self._current.pop(event.track_id, None)
            if wait is not None:
                wait.exit_time = event.timestamp
                self._history.append(wait)

    def current_wait(self, track_id: int) -> QueueWait | None:
        return self._current.get(track_id)

    def history(self, zone_id: str | None = None) -> list[QueueWait]:
        if zone_id is None:
            return list(self._history)
        return [wait for wait in self._history if wait.zone_id == zone_id]

    def average_waiting_time(self, zone_id: str | None = None) -> timedelta | None:
        waits = self.history(zone_id)
        if not waits:
            return None
        total = sum((wait.duration() for wait in waits), timedelta())
        return total / len(waits)

    def maximum_waiting_time(self, zone_id: str | None = None) -> timedelta | None:
        waits = self.history(zone_id)
        if not waits:
            return None
        return max(wait.duration() for wait in waits)

    def abandoned_waits(
        self, threshold: timedelta, zone_id: str | None = None
    ) -> list[QueueWait]:
        return [wait for wait in self.history(zone_id) if wait.duration() > threshold]
