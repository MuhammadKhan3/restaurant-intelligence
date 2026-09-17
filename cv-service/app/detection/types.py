"""Data types shared across the detection module."""

from dataclasses import dataclass

BoundingBox = tuple[int, int, int, int]  # x1, y1, x2, y2


@dataclass(frozen=True)
class Detection:
    """A single detected object in a frame."""

    bbox: BoundingBox
    confidence: float
    class_id: int
    class_name: str
