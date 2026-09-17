"""Estimates how many distinct parties are waiting, by clustering nearby people."""

import math

from app.tables.occupancy import person_center_point
from app.tracking.types import Track


def estimate_groups(tracks: list[Track], max_distance: float) -> list[list[int]]:
    """Cluster tracks into groups by transitive proximity of their center points.

    Two people within `max_distance` of each other are in the same group; group
    membership is transitive (A-B close and B-C close puts A, B, and C in one
    group even if A and C are far apart). This is a simple heuristic — spacing
    correlates with "traveling together" for a queue, but it is not certain.
    """
    if not tracks:
        return []

    centers = {track.track_id: person_center_point(track.bbox) for track in tracks}
    parent = {track_id: track_id for track_id in centers}

    def find(track_id: int) -> int:
        while parent[track_id] != track_id:
            parent[track_id] = parent[parent[track_id]]
            track_id = parent[track_id]
        return track_id

    def union(a: int, b: int) -> None:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    ids = list(centers)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            (x1, y1), (x2, y2) = centers[ids[i]], centers[ids[j]]
            if math.hypot(x1 - x2, y1 - y2) <= max_distance:
                union(ids[i], ids[j])

    groups: dict[int, list[int]] = {}
    for track_id in ids:
        groups.setdefault(find(track_id), []).append(track_id)

    return list(groups.values())
