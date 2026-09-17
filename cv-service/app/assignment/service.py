"""Assigns waiting groups to available tables and tracks walking→seated lifecycle."""

from collections.abc import Callable
from datetime import datetime

from app.assignment.matcher import find_available_tables, match_table_for_group
from app.assignment.models import AssignmentStatus, TableAssignment
from app.tables.models import TableZone
from app.tables.state import TableState, utc_now

Clock = Callable[[], datetime]


class TableAssignmentService:
    """Tracks one active assignment per table, from WALKING through SEATED.

    A table with an active assignment is excluded from further matching even
    if `table_states` still reports it AVAILABLE (occupancy detection lags
    behind an assignment being made).
    """

    def __init__(self, clock: Clock = utc_now) -> None:
        self._clock = clock
        self._assignments: dict[str, TableAssignment] = {}
        self._history: list[TableAssignment] = []

    def assign(
        self,
        group_track_ids: list[int],
        zones: list[TableZone],
        table_states: dict[str, TableState],
    ) -> TableAssignment | None:
        """Match `group_track_ids` to the best free table. None if no table fits."""
        available = [
            zone for zone in find_available_tables(zones, table_states)
            if zone.id not in self._assignments
        ]
        table = match_table_for_group(len(group_track_ids), available)
        if table is None:
            return None

        assignment = TableAssignment(
            zone_id=table.id, track_ids=list(group_track_ids), assigned_at=self._clock()
        )
        self._assignments[table.id] = assignment
        return assignment

    def confirm_seated(self, zone_id: str) -> TableAssignment | None:
        """Mark a WALKING assignment SEATED once the table's occupancy confirms it."""
        assignment = self._assignments.get(zone_id)
        if assignment is None or assignment.status == AssignmentStatus.SEATED:
            return None
        assignment.status = AssignmentStatus.SEATED
        assignment.seated_at = self._clock()
        return assignment

    def release(self, zone_id: str) -> TableAssignment | None:
        """Clear a table's assignment (it's free for matching again) into history."""
        assignment = self._assignments.pop(zone_id, None)
        if assignment is not None:
            self._history.append(assignment)
        return assignment

    def current_assignment(self, zone_id: str) -> TableAssignment | None:
        return self._assignments.get(zone_id)

    def history(self) -> list[TableAssignment]:
        return list(self._history)
