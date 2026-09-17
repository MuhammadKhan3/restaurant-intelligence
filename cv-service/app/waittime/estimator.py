"""Estimates how long a waiting group will wait for a table."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.assignment.matcher import find_available_tables, match_table_for_group
from app.tables.models import TableZone
from app.tables.state import TableState
from app.tables.timing import TableTimingTracker

DEFAULT_AVERAGE_TURNOVER = timedelta(minutes=45)


@dataclass(frozen=True)
class WaitEstimate:
    """An estimated wait for a group, and which table it's pinned to."""

    group_size: int
    wait: timedelta
    zone_id: str | None


class WaitTimeEstimator:
    """Combines current availability (capacity matching) with historical turnover
    (`TableTimingTracker`) to estimate when the next eligible table frees up.
    """

    def __init__(
        self,
        timing_tracker: TableTimingTracker,
        default_turnover: timedelta = DEFAULT_AVERAGE_TURNOVER,
    ) -> None:
        self._timing_tracker = timing_tracker
        self._default_turnover = default_turnover

    def average_turnover(self, zone_id: str) -> timedelta:
        """Average completed session duration for `zone_id`, or the default with no history."""
        sessions = self._timing_tracker.history(zone_id)
        if not sessions:
            return self._default_turnover
        total = sum((session.duration() for session in sessions), timedelta())
        return total / len(sessions)

    def estimate_wait(
        self,
        group_size: int,
        zones: list[TableZone],
        table_states: dict[str, TableState],
        now: datetime,
    ) -> WaitEstimate:
        """Estimate `group_size`'s wait. Raises ValueError if no configured table
        could ever seat a group this large.
        """
        eligible = [zone for zone in zones if zone.capacity >= group_size]
        if not eligible:
            raise ValueError("no configured table can seat a group of this size")

        available_now = find_available_tables(zones, table_states)
        immediate_match = match_table_for_group(group_size, available_now)
        if immediate_match is not None:
            return WaitEstimate(group_size=group_size, wait=timedelta(0), zone_id=immediate_match.id)

        candidates: list[tuple[timedelta, str]] = []
        for zone in eligible:
            if table_states.get(zone.id) != TableState.OCCUPIED:
                continue
            session = self._timing_tracker.current_session(zone.id)
            elapsed = session.duration(now) if session is not None else timedelta(0)
            remaining = max(timedelta(0), self.average_turnover(zone.id) - elapsed)
            candidates.append((remaining, zone.id))

        if not candidates:
            return WaitEstimate(group_size=group_size, wait=self._default_turnover, zone_id=None)

        remaining, zone_id = min(candidates, key=lambda pair: pair[0])
        return WaitEstimate(group_size=group_size, wait=remaining, zone_id=zone_id)
