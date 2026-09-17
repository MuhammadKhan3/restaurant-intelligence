"""Matches waiting groups to available tables by capacity."""

from app.tables.models import TableZone
from app.tables.state import TableState


def find_available_tables(
    zones: list[TableZone], table_states: dict[str, TableState]
) -> list[TableZone]:
    """Tables currently AVAILABLE, per a zone_id -> TableState mapping.

    A zone with no entry in `table_states` (never seen an occupancy update)
    is treated as not available.
    """
    return [zone for zone in zones if table_states.get(zone.id) == TableState.AVAILABLE]


def match_table_for_group(group_size: int, available_zones: list[TableZone]) -> TableZone | None:
    """The smallest-capacity available table that seats `group_size`, or None if none fit."""
    candidates = [zone for zone in available_zones if zone.capacity >= group_size]
    if not candidates:
        return None
    return min(candidates, key=lambda zone: zone.capacity)
