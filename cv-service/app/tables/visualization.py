"""Draws table zone polygons and labels onto a frame."""

import cv2
import numpy as np

from app.tables.models import TableZone

ZONE_COLOR = (255, 165, 0)


def draw_table_zones(frame: np.ndarray, zones: list[TableZone]) -> np.ndarray:
    """Return a copy of `frame` annotated with each table zone's polygon."""

    annotated = frame.copy()

    for zone in zones:
        points = np.array(zone.points, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(annotated, [points], isClosed=True, color=ZONE_COLOR, thickness=2)

        label = f"{zone.name} ({zone.capacity})"
        label_origin = zone.points[0]
        cv2.putText(
            annotated,
            label,
            label_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            ZONE_COLOR,
            1,
            cv2.LINE_AA,
        )

    return annotated
