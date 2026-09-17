"""Draws tracking bounding boxes and persistent IDs onto a frame."""

import cv2
import numpy as np

from app.tracking.types import Track


def draw_tracks(frame: np.ndarray, tracks: list[Track]) -> np.ndarray:
    """Return a copy of `frame` annotated with each track's box and ID."""

    annotated = frame.copy()

    for track in tracks:
        color = _color_for_id(track.track_id)
        x1, y1, x2, y2 = track.bbox
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        label = f"ID {track.track_id} {track.class_name} {track.confidence:.2f}"
        label_origin = (x1, max(y1 - 10, 0))
        cv2.putText(
            annotated,
            label,
            label_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )

    return annotated


def _color_for_id(track_id: int) -> tuple[int, int, int]:
    """Deterministic color per track ID, so a person's box stays one color."""
    rng = np.random.default_rng(track_id)
    b, g, r = rng.integers(64, 256, size=3).tolist()
    return (b, g, r)
