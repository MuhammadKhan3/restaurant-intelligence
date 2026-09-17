"""Table occupancy state machine: debounced transitions and state history."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum

from app.tables.occupancy import TableOccupancy

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TableState(StrEnum):
    """A table zone's current operational state."""

    AVAILABLE = "available"
    OCCUPIED = "occupied"
    CLEANING = "cleaning"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


MANUAL_STATES = frozenset({TableState.CLEANING, TableState.BLOCKED})


@dataclass(frozen=True)
class StateChange:
    """A single recorded state transition for a table zone."""

    zone_id: str
    from_state: TableState
    to_state: TableState
    timestamp: datetime


@dataclass
class _ZoneState:
    confirmed: TableState = TableState.UNKNOWN
    pending: TableState | None = None
    pending_count: int = 0
    history: list[StateChange] = field(default_factory=list)


class TableStateManager:
    """Derives debounced AVAILABLE/OCCUPIED state per zone and tracks history.

    Automatic transitions come from `update()`, which only toggles between
    AVAILABLE and OCCUPIED once the observed occupancy has been consistent for
    `debounce_frames` consecutive calls, to absorb detection flicker. CLEANING
    and BLOCKED are manual overrides set by staff via `set_manual_state()`; while
    a zone is in one of those states, automatic occupancy updates are ignored
    until the override is cleared with `clear_manual_state()`.
    """

    def __init__(self, debounce_frames: int = 3, clock: Clock = utc_now) -> None:
        if debounce_frames < 1:
            raise ValueError("debounce_frames must be at least 1")
        self._debounce_frames = debounce_frames
        self._clock = clock
        self._zones: dict[str, _ZoneState] = {}

    def _zone_state(self, zone_id: str) -> _ZoneState:
        return self._zones.setdefault(zone_id, _ZoneState())

    def _transition(self, zone_id: str, zone: _ZoneState, to_state: TableState) -> None:
        if to_state == zone.confirmed:
            zone.pending = None
            zone.pending_count = 0
            return

        change = StateChange(
            zone_id=zone_id,
            from_state=zone.confirmed,
            to_state=to_state,
            timestamp=self._clock(),
        )
        zone.confirmed = to_state
        zone.pending = None
        zone.pending_count = 0
        zone.history.append(change)

    def update(self, occupancy_results: list[TableOccupancy]) -> dict[str, TableState]:
        """Feed one frame's occupancy results and return each zone's confirmed state."""
        for result in occupancy_results:
            zone = self._zone_state(result.zone_id)
            if zone.confirmed in MANUAL_STATES:
                continue

            observed = TableState.OCCUPIED if result.occupied else TableState.AVAILABLE

            if observed == zone.pending:
                zone.pending_count += 1
            else:
                zone.pending = observed
                zone.pending_count = 1

            if zone.pending_count >= self._debounce_frames:
                self._transition(result.zone_id, zone, observed)

        return {zone_id: zone.confirmed for zone_id, zone in self._zones.items()}

    def set_manual_state(self, zone_id: str, state: TableState) -> None:
        """Force a zone into CLEANING or BLOCKED, overriding automatic detection."""
        if state not in MANUAL_STATES:
            raise ValueError(f"{state} is not a manual state; use update() instead")
        zone = self._zone_state(zone_id)
        self._transition(zone_id, zone, state)

    def clear_manual_state(self, zone_id: str) -> None:
        """Release a CLEANING/BLOCKED override, returning the zone to UNKNOWN.

        The zone resumes automatic tracking from UNKNOWN; the next `update()`
        calls must re-confirm AVAILABLE or OCCUPIED through the normal debounce.
        """
        zone = self._zone_state(zone_id)
        if zone.confirmed in MANUAL_STATES:
            self._transition(zone_id, zone, TableState.UNKNOWN)

    def current_state(self, zone_id: str) -> TableState:
        zone = self._zones.get(zone_id)
        return zone.confirmed if zone else TableState.UNKNOWN

    def history(self, zone_id: str) -> list[StateChange]:
        zone = self._zones.get(zone_id)
        return list(zone.history) if zone else []
