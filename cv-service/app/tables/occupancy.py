"""Table occupancy detection: assign tracked people to table zones."""

from dataclasses import dataclass

from app.detection.types import BoundingBox
from app.tables.models import TableZone
from app.tracking.types import Track


def person_center_point(bbox: BoundingBox) -> tuple[float, float]:
    """Return the center point (x, y) of a person's bounding box."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def point_in_polygon(point: tuple[float, float], polygon: list[tuple[int, int]]) -> bool:
    """Ray-casting point-in-polygon test. Points on an edge are treated as inside."""
    x, y = point
    inside = False
    n = len(polygon)

    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]

        if (y1 == y2 == y) and min(x1, x2) <= x <= max(x1, x2):
            return True

        if (y1 > y) != (y2 > y):
            x_intersect = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x == x_intersect:
                return True
            if x < x_intersect:
                inside = not inside

    return inside


def assign_people_to_tables(
    tracks: list[Track], zones: list[TableZone]
) -> dict[str, list[int]]:
    """Assign each track to the first table zone whose polygon contains its center point.

    A track whose center point falls in no zone is omitted. If zones overlap, a
    track is assigned to whichever zone appears first in `zones`.
    """
    assignments: dict[str, list[int]] = {zone.id: [] for zone in zones}

    for track in tracks:
        center = person_center_point(track.bbox)
        for zone in zones:
            if point_in_polygon(center, zone.points):
                assignments[zone.id].append(track.track_id)
                break

    return assignments


@dataclass(frozen=True)
class TableOccupancy:
    """Occupancy result for a single table zone."""

    zone_id: str
    person_count: int
    occupied: bool
    track_ids: list[int]


def detect_table_occupancy(
    tracks: list[Track], zones: list[TableZone], occupancy_threshold: int = 1
) -> list[TableOccupancy]:
    """Determine occupied/available state for each table zone.

    A zone is `occupied` when the number of people assigned to it meets or
    exceeds `occupancy_threshold`.
    """
    assignments = assign_people_to_tables(tracks, zones)

    return [
        TableOccupancy(
            zone_id=zone.id,
            person_count=len(assignments[zone.id]),
            occupied=len(assignments[zone.id]) >= occupancy_threshold,
            track_ids=assignments[zone.id],
        )
        for zone in zones
    ]
