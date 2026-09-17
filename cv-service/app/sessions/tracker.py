"""Tracks each table's continuous customer dining session, resilient to brief occlusion.

Two independent grace mechanisms combine to satisfy "a brief disappearance is
not a departure":

- Per-customer: `TrackLifecycleManager` (Phase 4) keeps an occluded track
  alive as LOST (not REMOVED) at its last known position for
  `max_lost_frames`, so it still counts as present in whatever zone it's in.
  Feed this tracker the *lifecycle manager's* output (ACTIVE + LOST), not just
  its `active_tracks()`, or occlusion resilience is lost.
- Per-table: `TableSessionTracker` (this module) additionally waits
  `empty_grace_period` of continuous *wall-clock* time after a zone reports
  zero assigned customers before ending the whole table's session, covering
  gaps that outlast any single track's lifecycle (e.g. everyone is briefly
  blocked from view at once).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.sessions.models import CustomerSession, SessionStatus
from app.tables.state import utc_now

Clock = Callable[[], datetime]


@dataclass
class _ActiveSession:
    session: CustomerSession
    current_track_ids: set[int] = field(default_factory=set)
    empty_since: datetime | None = None


class TableSessionTracker:
    """One continuous `CustomerSession` per table, spanning brief occlusion gaps.

    Call `update(zone_id, assigned_track_ids, now)` once per tick per zone,
    with the current set of track ids assigned to that zone (see module
    docstring for what to include). A zone transitioning from no active
    session to having assigned tracks starts a new session (a "new group");
    one that stays empty for `empty_grace_period` ends the current session.
    """

    def __init__(self, empty_grace_period: timedelta, clock: Clock = utc_now) -> None:
        self._grace_period = empty_grace_period
        self._clock = clock
        self._active: dict[str, _ActiveSession] = {}
        self._history: dict[str, list[CustomerSession]] = {}

    def update(
        self, zone_id: str, assigned_track_ids: list[int], now: datetime | None = None
    ) -> None:
        now = now if now is not None else self._clock()
        state = self._active.get(zone_id)

        if assigned_track_ids:
            if state is None:
                session = CustomerSession(
                    zone_id=zone_id,
                    started_at=now,
                    track_ids=frozenset(assigned_track_ids),
                    peak_customer_count=len(assigned_track_ids),
                )
                self._active[zone_id] = _ActiveSession(
                    session=session, current_track_ids=set(assigned_track_ids)
                )
                return

            state.empty_since = None
            state.current_track_ids = set(assigned_track_ids)
            state.session.track_ids = state.session.track_ids | frozenset(assigned_track_ids)
            state.session.peak_customer_count = max(
                state.session.peak_customer_count, len(assigned_track_ids)
            )
            return

        if state is None:
            return

        if state.empty_since is None:
            state.empty_since = now
            state.current_track_ids = set()
            return

        if now - state.empty_since >= self._grace_period:
            state.session.ended_at = state.empty_since
            state.session.status = SessionStatus.COMPLETED
            self._history.setdefault(zone_id, []).append(state.session)
            del self._active[zone_id]

    def current_session(self, zone_id: str) -> CustomerSession | None:
        state = self._active.get(zone_id)
        return state.session if state is not None else None

    def current_customer_count(self, zone_id: str) -> int:
        """Customers assigned to the zone right now (0 during a grace-period gap).

        For the group's representative size (e.g. to display "Customers: 3"
        for the whole visit), prefer `current_session(zone_id).peak_customer_count`.
        """
        state = self._active.get(zone_id)
        return len(state.current_track_ids) if state is not None else 0

    def history(self, zone_id: str | None = None) -> list[CustomerSession]:
        if zone_id is None:
            return [session for sessions in self._history.values() for session in sessions]
        return list(self._history.get(zone_id, []))
