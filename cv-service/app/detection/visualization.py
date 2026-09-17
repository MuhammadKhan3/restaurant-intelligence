"""Draws detection bounding boxes and labels onto a frame."""

import cv2
import numpy as np

from app.detection.types import Detection

BOX_COLOR = (0, 255, 0)
TEXT_COLOR = (0, 255, 0)


def draw_detections(frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
    """Return a copy of `frame` annotated with bounding boxes and labels."""

    annotated = frame.copy()

    for detection in detections:
        x1, y1, x2, y2 = detection.bbox
        cv2.rectangle(annotated, (x1, y1), (x2, y2), BOX_COLOR, 2)

        label = f"{detection.class_name} {detection.confidence:.2f}"
        label_origin = (x1, max(y1 - 10, 0))
        cv2.putText(
            annotated,
            label,
            label_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            TEXT_COLOR,
            1,
            cv2.LINE_AA,
        )

    return annotated
